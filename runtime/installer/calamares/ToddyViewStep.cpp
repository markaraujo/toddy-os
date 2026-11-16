// Original project UI/job. No copied upstream implementation or arbitrary hooks.
#include "ToddyViewStep.h"
#include <GlobalStorage.h>
#include <Job.h>
#include <JobQueue.h>
#include <QCheckBox>
#include <QCloseEvent>
#include <QDialog>
#include <QPointer>
#include <QComboBox>
#include <QCoreApplication>
#include <QFile>
#include <QFormLayout>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QLineEdit>
#include <QLocale>
#include <QPlainTextEdit>
#include <QProcess>
#include <QProcessEnvironment>
#include <QPushButton>
#include <QRegularExpression>
#include <QSignalBlocker>
#include <QTimer>
#include <QUuid>
#include <QVBoxLayout>
#include <QWidget>
#include <array>
#include <atomic>
#include <cerrno>
#include <fcntl.h>
#include <functional>
#include <memory>
#include <mutex>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/resource.h>
#include <stdexcept>
#include <time.h>
#include <unistd.h>

namespace {
const QString backend = QStringLiteral("/usr/lib/toddy/installer/calamares/cli.py");
const QString resultKey = QStringLiteral("toddy.installResultJson");
QString copy(const char* key)
{
    static const QJsonObject catalog = [] {
        QFile file(QStringLiteral("/usr/share/calamares/modules/toddy/strings.json"));
        if (!file.open(QIODevice::ReadOnly) || file.size() > 131072) return QJsonObject();
        return QJsonDocument::fromJson(file.readAll()).object();
    }();
    const auto language = QLocale().language() == QLocale::Portuguese ? QStringLiteral("pt-BR") : QStringLiteral("en");
    return catalog.value(language).toObject().value(QString::fromLatin1(key)).toString(QString::fromLatin1(key));
}
qint64 monotonicMs()
{
    timespec value {};
    if (::clock_gettime(CLOCK_MONOTONIC, &value) != 0) return -1;
    return qint64(value.tv_sec) * 1000 + value.tv_nsec / 1000000;
}
qint64 startTicks()
{
    QFile file(QStringLiteral("/proc/self/stat"));
    if (!file.open(QIODevice::ReadOnly)) return -1;
    const auto raw = file.readAll();
    const auto position = raw.lastIndexOf(") ");
    const auto fields = raw.mid(position + 2).simplified().split(' ');
    bool ok = false;
    const auto ticks = fields.size() > 19 ? fields[19].toLongLong(&ok) : -1;
    return ok ? ticks : -1;
}
QByteArray bootId()
{
    QFile file(QStringLiteral("/proc/sys/kernel/random/boot_id"));
    return file.open(QIODevice::ReadOnly) ? file.readAll().trimmed() : QByteArray();
}
int sealed(const QByteArray& data)
{
    if (data.isEmpty() || data.size() > 32768) return -1;
    const int descriptor = ::memfd_create("toddy-install-plan", MFD_CLOEXEC | MFD_ALLOW_SEALING);
    if (descriptor < 0) return -1;
    bool ok = ::fchmod(descriptor, 0600) == 0;
    qsizetype written = 0;
    while (ok && written < data.size()) {
        const auto count = ::write(descriptor, data.constData() + written, size_t(data.size() - written));
        if (count <= 0) ok = false;
        else written += count;
    }
    ok = ok && ::fcntl(descriptor, F_ADD_SEALS, F_SEAL_WRITE | F_SEAL_GROW | F_SEAL_SHRINK | F_SEAL_SEAL) == 0;
    if (!ok) { ::close(descriptor); return -1; }
    return descriptor;
}
void inherit(QProcess& process, const std::array<int, 4>& descriptors)
{
    process.setChildProcessModifier([descriptors] {
        // Only async-signal-safe descriptor operations in this fork callback.
        for (const int descriptor : descriptors) {
            if (descriptor < 0) continue;
            const auto flags = ::fcntl(descriptor, F_GETFD);
            if (flags < 0 || ::fcntl(descriptor, F_SETFD, flags & ~FD_CLOEXEC) < 0) ::_exit(125);
        }
    });
}
QProcessEnvironment environment()
{
    QProcessEnvironment result;
    result.insert(QStringLiteral("PATH"), QStringLiteral("/usr/sbin:/usr/bin"));
    result.insert(QStringLiteral("HOME"), QStringLiteral("/root"));
    result.insert(QStringLiteral("LANG"), QStringLiteral("C.UTF-8"));
    // No inherited owner session bus, keyring, token, proxy, Python or loader
    // environment. This child is a headless root backend, not the Qt GUI.
    return result;
}
void closeAll(const std::array<int, 4>& descriptors)
{
    for (const int descriptor : descriptors) if (descriptor >= 0) ::close(descriptor);
}
}

struct ToddyInstallState
{
    mutable std::mutex mutex;
    QByteArray plan;
    qint64 confirmedAt = -1;
    int credential = -1;
    int cancelRead = -1;
    int cancelWrite = -1;
    std::atomic_bool canceled {false};
    std::function<void(bool)> showStop;  // Immutable callback queues GUI work.
    ~ToddyInstallState() { clear(); }
    void clear()
    {
        std::lock_guard<std::mutex> guard(mutex);
        for (int* descriptor : {&credential, &cancelRead, &cancelWrite}) {
            if (*descriptor >= 0) ::close(*descriptor);
            *descriptor = -1;
        }
        plan.clear(); confirmedAt = -1;
    }
    void requestCancel()
    {
        canceled = true;
        std::lock_guard<std::mutex> guard(mutex);
        // Retain our read endpoint until cleanup, avoiding SIGPIPE on a raced
        // post-completion click. The pipe is nonblocking and carries no secret.
        if (cancelWrite >= 0) { const char stop = 'x'; const auto ignored = ::write(cancelWrite, &stop, 1); Q_UNUSED(ignored); }
    }
};

// Calamares generic Cancel exits the application and terminates its job thread.
// During exec this independent dialog requests a safe boundary without exiting.
class SafeStopDialog final : public QDialog
{
public:
    explicit SafeStopDialog(QWidget* parent) : QDialog(parent)
    {
        setWindowTitle(copy("job")); setModal(false);
        setWindowFlags(Qt::Window | Qt::CustomizeWindowHint | Qt::WindowTitleHint);
        auto* layout = new QVBoxLayout(this);
        m_label = new QLabel(copy("stop_explanation")); m_label->setWordWrap(true); layout->addWidget(m_label);
        m_stop = new QPushButton(copy("stop")); layout->addWidget(m_stop);
        connect(m_stop, &QPushButton::clicked, this, [this] { reject(); });
    }
    std::function<void()> cancel;
    void reject() override
    {
        if (cancel) cancel();
        m_stop->setEnabled(false); m_label->setText(copy("stop_waiting"));
    }
protected:
    void closeEvent(QCloseEvent* event) override { reject(); event->ignore(); }
private:
    QLabel* m_label;
    QPushButton* m_stop;
};

class ToddyInstallJob final : public Calamares::Job
{
public:
    explicit ToddyInstallJob(std::shared_ptr<ToddyInstallState> state) : m_state(std::move(state)) {}
    QString prettyName() const override { return copy("job"); }
    QString prettyStatusMessage() const override { return copy("writing"); }
    Calamares::JobResult exec() override
    {
        QByteArray planBytes;
        qint64 issued = -1;
        int password = -1, cancellation = -1;
        {
            std::lock_guard<std::mutex> guard(m_state->mutex);
            planBytes = m_state->plan; issued = m_state->confirmedAt;
            if (m_state->credential >= 0) password = ::fcntl(m_state->credential, F_DUPFD_CLOEXEC, 3);
            if (m_state->cancelRead >= 0) cancellation = ::fcntl(m_state->cancelRead, F_DUPFD_CLOEXEC, 3);
        }
        const auto plan = QJsonDocument::fromJson(planBytes).object();
        const auto planHash = plan.value(QStringLiteral("plan_sha256")).toString();
        const auto serial = plan.value(QStringLiteral("target")).toObject().value(QStringLiteral("serial")).toString();
        if (m_state->canceled || password < 0 || cancellation < 0 || issued < 0 ||
            !QRegularExpression(QStringLiteral("^[0-9a-f]{64}$")).match(planHash).hasMatch()) {
            if (password >= 0) ::close(password);
            if (cancellation >= 0) ::close(cancellation);
            return Calamares::JobResult::error(copy("not_confirmed"));
        }
        const QJsonObject confirmation {{"version", 1}, {"plan_sha256", planHash}, {"target_serial", serial},
            {"creator_pid", qint64(::getpid())}, {"creator_start_ticks", startTicks()}, {"boot_id", QString::fromLatin1(bootId())},
            {"issued_monotonic_ms", issued}, {"expires_monotonic_ms", issued + 600000}};
        std::array<int, 4> descriptors {sealed(planBytes), sealed(QJsonDocument(confirmation).toJson(QJsonDocument::Compact)), password, cancellation};
        if (descriptors[0] < 0 || descriptors[1] < 0) {
            closeAll(descriptors); return Calamares::JobResult::error(copy("private_input_failed"));
        }
        QProcess child;
        child.setProcessEnvironment(environment());
        child.setStandardInputFile(QProcess::nullDevice());
        child.setProgram(QStringLiteral("/usr/bin/python3"));
        child.setArguments({QStringLiteral("-I"), backend, QStringLiteral("execute"),
            QStringLiteral("--plan-fd"), QString::number(descriptors[0]),
            QStringLiteral("--confirmation-fd"), QString::number(descriptors[1]),
            QStringLiteral("--credential-fd"), QString::number(descriptors[2]),
            QStringLiteral("--cancel-fd"), QString::number(descriptors[3])});
        inherit(child, descriptors);
        child.start();
        if (!child.waitForStarted(5000)) {
            closeAll(descriptors); m_state->clear(); return Calamares::JobResult::error(copy("backend_unavailable"));
        }
        if (m_state->showStop) m_state->showStop(true);
        QByteArray buffer;
        QJsonObject final;
        bool protocolError = false;
        qsizetype outputBytes = 0, errorBytes = 0;
        const auto drain = [&] {
            while (child.bytesAvailable() > 0) {
                const auto piece = child.read(4096);
                outputBytes += piece.size();
                if (outputBytes > 65536) { protocolError = true; m_state->requestCancel(); continue; }
                buffer += piece;
                qsizetype end;
                while ((end = buffer.indexOf('\n')) >= 0) {
                    const auto line = buffer.left(end); buffer.remove(0, end + 1);
                    const auto document = QJsonDocument::fromJson(line);
                    const auto value = document.object();
                    if (!document.isObject() || value.value("version").toInt(-1) != 1 ||
                        value.value("operation_id").toString() != plan.value("options").toObject().value("operation_id").toString()) {
                        protocolError = true; m_state->requestCancel(); continue;
                    }
                    if (value.value("kind").toString() == QStringLiteral("progress")) {
                        const int progressValue = value.value("progress_milli").toInt(-1);
                        if (progressValue < 0 || progressValue > 1000) { protocolError = true; m_state->requestCancel(); }
                        else emit progress(progressValue / 1000.0);
                    } else if (value.value("kind").toString() == QStringLiteral("result") && final.isEmpty()) final = value;
                    else { protocolError = true; m_state->requestCancel(); }
                }
            }
            // Discard raw native diagnostics; never forward command output or a
            // login password to Calamares debug/global storage.
            errorBytes += child.readAllStandardError().size();
            if (errorBytes > 65536) { protocolError = true; m_state->requestCancel(); }
        };
        while (child.state() != QProcess::NotRunning) { child.waitForFinished(100); drain(); }
        drain(); closeAll(descriptors); m_state->clear();
        if (m_state->showStop) m_state->showStop(false);
        if (!buffer.isEmpty()) protocolError = true;
        if (protocolError || child.exitStatus() != QProcess::NormalExit || child.exitCode() != 0 ||
            final.value("state").toString() != QStringLiteral("completed")) {
            // No kill()/timeout on a disk writer. Safe-boundary cancellation and
            // journal reconciliation remain authoritative; never show success.
            return Calamares::JobResult::error(copy("not_completed"), copy("rescue"));
        }
        Calamares::JobQueue::instance()->globalStorage()->insert(resultKey,
            QString::fromUtf8(QJsonDocument(final).toJson(QJsonDocument::Compact)));
        return Calamares::JobResult::ok();
    }
private:
    std::shared_ptr<ToddyInstallState> m_state;
};

ToddyViewStep::ToddyViewStep(QObject* parent) : Calamares::ViewStep(parent), m_state(std::make_shared<ToddyInstallState>())
{
    const rlimit limit {0, 0};
    if (::setrlimit(RLIMIT_CORE, &limit) != 0) throw std::runtime_error("private_installer_core_limit_unavailable");
}
ToddyViewStep::~ToddyViewStep() = default;
QString ToddyViewStep::prettyName() const { return copy(m_finished ? "finished" : "title"); }
QString ToddyViewStep::prettyStatus() const { return m_finished ? copy("boot_pending") : copy("review_warning"); }
bool ToddyViewStep::isBackEnabled() const { return !m_finished && !m_query; }
bool ToddyViewStep::isNextEnabled() const
{
    if (m_finished) return true;
    if (!m_widget || m_query || m_plan.isEmpty() || !m_confirm->isChecked() || m_state->canceled) return false;
    {
        std::lock_guard<std::mutex> guard(m_state->mutex);
        if (m_state->credential >= 0 && m_state->plan == m_plan && m_state->confirmedAt >= 0) return true;
    }
    const auto password = m_password->text().toUtf8();
    return password.size() >= 12 && password.size() <= 1024 && !password.contains('\n') && !password.contains('\r') && !password.contains('\0') &&
        m_password->text() == m_passwordAgain->text();
}
void ToddyViewStep::setConfigurationMap(const QVariantMap& configuration)
{
    const auto mode = configuration.value(QStringLiteral("mode")).toString();
    m_finished = mode == QStringLiteral("finished");
}
QWidget* ToddyViewStep::widget()
{
    if (m_widget) return m_widget;
    m_widget = new QWidget;
    auto* layout = new QVBoxLayout(m_widget);
    m_status = new QLabel(copy(m_finished ? "not_completed" : "review_warning")); m_status->setWordWrap(true); layout->addWidget(m_status);
    if (m_finished) return m_widget;
    auto* stopDialog = new SafeStopDialog(m_widget);
    const std::weak_ptr<ToddyInstallState> weakState(m_state);
    stopDialog->cancel = [weakState] { if (const auto state = weakState.lock()) state->requestCancel(); };
    const QPointer<SafeStopDialog> stopPointer(stopDialog);
    m_state->showStop = [stopPointer](bool visible) {
        QMetaObject::invokeMethod(QCoreApplication::instance(), [stopPointer, visible] {
            if (!stopPointer) return;
            if (visible) { stopPointer->show(); stopPointer->raise(); }
            else stopPointer->hide();
        }, Qt::QueuedConnection);
    };
    auto* form = new QFormLayout;
    m_disk = new QComboBox; m_disk->addItem(copy("choose_disk"), QString()); form->addRow(copy("disk"), m_disk);
    m_boot = new QComboBox; m_boot->addItem(QStringLiteral("UEFI"), QStringLiteral("uefi")); m_boot->addItem(QStringLiteral("BIOS / GPT"), QStringLiteral("bios"));
    m_boot->setCurrentIndex(QFile::exists(QStringLiteral("/sys/firmware/efi")) ? 0 : 1); form->addRow(copy("firmware"), m_boot);
    m_user = new QLineEdit(QStringLiteral("owner")); m_user->setMaxLength(32); form->addRow(copy("username"), m_user);
    m_host = new QLineEdit(QStringLiteral("toddy-os")); m_host->setMaxLength(63); form->addRow(copy("hostname"), m_host);
    m_locale = new QComboBox; m_locale->addItem(QStringLiteral("English"), QStringLiteral("en_US.UTF-8")); m_locale->addItem(QStringLiteral("Português"), QStringLiteral("pt_BR.UTF-8")); form->addRow(copy("locale"), m_locale);
    m_timezone = new QLineEdit(QStringLiteral("UTC")); m_timezone->setMaxLength(128); form->addRow(copy("timezone"), m_timezone);
    m_ai = new QComboBox; m_ai->addItem(copy("later"), QStringLiteral("later")); m_ai->addItem(copy("api"), QStringLiteral("api")); m_ai->addItem(copy("local"), QStringLiteral("local")); form->addRow(copy("assistant"), m_ai);
    m_docker = new QCheckBox(QStringLiteral("Docker")); m_opencode = new QCheckBox(QStringLiteral("OpenCode")); m_vscode = new QCheckBox(QStringLiteral("VS Code"));
    for (auto* extra : {m_docker, m_opencode, m_vscode}) form->addRow(copy("deferred_extra"), extra);
    m_password = new QLineEdit; m_passwordAgain = new QLineEdit;
    for (auto* field : {m_password, m_passwordAgain}) { field->setEchoMode(QLineEdit::Password); field->setMaxLength(1024); }
    form->addRow(copy("login_password"), m_password); form->addRow(copy("repeat_password"), m_passwordAgain);
    layout->addLayout(form);
    auto* button = new QPushButton(copy("review")); layout->addWidget(button);
    m_review = new QPlainTextEdit; m_review->setReadOnly(true); layout->addWidget(m_review);
    m_confirm = new QCheckBox(copy("confirm")); layout->addWidget(m_confirm);
    connect(button, &QPushButton::clicked, this, &ToddyViewStep::review);
    for (auto* field : {m_user, m_host, m_timezone}) connect(field, &QLineEdit::textChanged, this, &ToddyViewStep::invalidateReview);
    for (auto* choice : {m_disk, m_boot, m_locale, m_ai}) connect(choice, &QComboBox::currentIndexChanged, this, &ToddyViewStep::invalidateReview);
    for (auto* choice : {m_docker, m_opencode, m_vscode}) connect(choice, &QCheckBox::toggled, this, &ToddyViewStep::invalidateReview);
    for (auto* field : {m_password, m_passwordAgain}) connect(field, &QLineEdit::textChanged, this, [this] { emit nextStatusChanged(isNextEnabled()); });
    connect(m_confirm, &QCheckBox::toggled, this, [this] { emit nextStatusChanged(isNextEnabled()); });
    return m_widget;
}
void ToddyViewStep::status(const QString& message) { if (m_status) m_status->setText(message); }
void ToddyViewStep::invalidateReview()
{
    ++m_generation; m_plan.clear(); if (m_confirm) m_confirm->setChecked(false); emit nextStatusChanged(false);
}
void ToddyViewStep::onActivate()
{
    widget();
    if (m_finished) {
        const auto raw = Calamares::JobQueue::instance()->globalStorage()->value(resultKey).toString().toUtf8();
        const auto result = QJsonDocument::fromJson(raw).object();
        status(result.value("state").toString() == QStringLiteral("completed") ? copy("boot_pending") : copy("not_completed"));
        return;
    }
    Calamares::JobQueue::instance()->globalStorage()->remove(resultKey);
    m_state->clear(); m_state->canceled = false; invalidateReview(); query(QStringLiteral("targets"));
}
void ToddyViewStep::review()
{
    if (m_query || m_disk->currentData().toString().isEmpty()) return;
    QJsonArray extras;
    if (m_docker->isChecked()) extras.append(QStringLiteral("docker"));
    if (m_opencode->isChecked()) extras.append(QStringLiteral("opencode"));
    if (m_vscode->isChecked()) extras.append(QStringLiteral("vscode"));
    const QJsonObject options {{"operation_id", QUuid::createUuid().toString(QUuid::Id128)}, {"boot_mode", m_boot->currentData().toString()},
        {"username", m_user->text()}, {"uid", 1000}, {"gid", 1000}, {"locale", m_locale->currentData().toString()},
        {"timezone", m_timezone->text()}, {"hostname", m_host->text()}, {"ai_choice", m_ai->currentData().toString()}, {"extras", extras}};
    const QJsonObject input {{"device", m_disk->currentData().toString()}, {"options", options}};
    invalidateReview(); query(QStringLiteral("review"), QJsonDocument(input).toJson(QJsonDocument::Compact));
}
void ToddyViewStep::query(const QString& action, const QByteArray& body)
{
    if (m_query) return;
    status(copy("checking"));
    auto* process = new QProcess(this); m_query = process;
    const int descriptor = body.isEmpty() ? -1 : sealed(body);
    if (!body.isEmpty() && descriptor < 0) { m_query = nullptr; process->deleteLater(); status(copy("private_input_failed")); return; }
    process->setProcessEnvironment(environment()); process->setStandardInputFile(QProcess::nullDevice());
    process->setProgram(QStringLiteral("/usr/bin/python3"));
    QStringList arguments {QStringLiteral("-I"), backend, action};
    if (descriptor >= 0) arguments << QStringLiteral("--options-fd") << QString::number(descriptor);
    process->setArguments(arguments); inherit(*process, {descriptor, -1, -1, -1});
    auto buffer = std::make_shared<QByteArray>();
    auto ownedDescriptor = std::make_shared<std::atomic<int>>(descriptor);
    const auto generation = m_generation;
    connect(process, &QProcess::readyReadStandardOutput, this, [this, process, buffer] {
        *buffer += process->readAllStandardOutput();
        if (buffer->size() > 32768) process->kill();  // This query is strictly read-only.
    });
    connect(process, &QProcess::finished, this, [this, process, buffer, ownedDescriptor, action, generation](int code, QProcess::ExitStatus exit) {
        *buffer += process->readAllStandardOutput(); process->readAllStandardError();
        const int toClose = ownedDescriptor->exchange(-1);
        if (toClose >= 0) ::close(toClose);
        m_query = nullptr;
        const auto result = buffer->size() <= 32768 ? QJsonDocument::fromJson(buffer->trimmed()).object() : QJsonObject();
        if (code != 0 || exit != QProcess::NormalExit || result.value("version").toInt(-1) != 1) status(copy("unavailable"));
        else if (action == QStringLiteral("targets")) {
            m_disk->clear(); m_disk->addItem(copy("choose_disk"), QString());
            for (const auto& item : result.value("targets").toArray()) {
                const auto disk = item.toObject();
                m_disk->addItem(disk.value("path").toString() + QStringLiteral(" · ") + disk.value("serial").toString() + QStringLiteral(" · ") +
                    QString::number(disk.value("size").toDouble() / (1024 * 1024 * 1024), 'f', 1) + QStringLiteral(" GiB"), disk.value("path").toString());
            }
            status(copy("review_warning"));
        } else if (generation != m_generation) {
            status(copy("review_warning"));  // Changed inputs cannot adopt a stale review.
        } else if (result.value("state").toString() == QStringLiteral("review_required") && result.value("disk_writes").isBool() && !result.value("disk_writes").toBool()) {
            m_plan = result.value("plan_json").toString().toUtf8();
            m_review->setPlainText(QString::fromUtf8(QJsonDocument::fromJson(m_plan).toJson(QJsonDocument::Indented)));
            status(copy("review_warning"));
        } else status(copy("unavailable"));
        process->deleteLater(); emit nextStatusChanged(isNextEnabled());
    });
    connect(process, &QProcess::errorOccurred, this, [this, process, ownedDescriptor](QProcess::ProcessError error) {
        if (error != QProcess::FailedToStart) return;
        const int toClose = ownedDescriptor->exchange(-1);
        if (toClose >= 0) ::close(toClose);
        m_query = nullptr; status(copy("backend_unavailable")); process->deleteLater(); emit nextStatusChanged(false);
    });
    QTimer::singleShot(30000, process, [process] { if (process->state() != QProcess::NotRunning) process->kill(); });
    process->start(); emit nextStatusChanged(false);
}
void ToddyViewStep::onLeave()
{
    if (m_finished || !isNextEnabled()) return;
    int credentials[2] {-1, -1}, control[2] {-1, -1};
    if (::pipe2(credentials, O_CLOEXEC) != 0 || ::pipe2(control, O_CLOEXEC | O_NONBLOCK) != 0) {
        for (const int descriptor : {credentials[0], credentials[1], control[0], control[1]}) if (descriptor >= 0) ::close(descriptor);
        invalidateReview(); status(copy("private_input_failed")); return;
    }
    auto password = m_password->text().toUtf8();
    const auto written = ::write(credentials[1], password.constData(), size_t(password.size()));
    const bool ok = written == password.size(); password.fill('\0');
    ::close(credentials[1]);
    const QSignalBlocker firstSecret(m_password), secondSecret(m_passwordAgain);
    m_password->clear(); m_passwordAgain->clear();
    if (!ok) { ::close(credentials[0]); ::close(control[0]); ::close(control[1]); invalidateReview(); return; }
    m_state->clear();
    std::lock_guard<std::mutex> guard(m_state->mutex);
    m_state->plan = m_plan; m_state->confirmedAt = monotonicMs();
    m_state->credential = credentials[0]; m_state->cancelRead = control[0]; m_state->cancelWrite = control[1];
}
Calamares::JobList ToddyViewStep::jobs() const
{
    if (m_finished) return {};
    return Calamares::JobList() << Calamares::job_ptr(new ToddyInstallJob(m_state));
}
void ToddyViewStep::onCancel()
{
    if (m_query) m_query->kill();  // Read-only discovery/review only.
    m_state->requestCancel();     // The install writer uses its safe boundary.
    if (m_password) { m_password->clear(); m_passwordAgain->clear(); }
}

CALAMARES_PLUGIN_FACTORY_DEFINITION(ToddyViewStepFactory, registerPlugin<ToddyViewStep>())
