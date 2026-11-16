#pragma once
// Original Toddy project module against the frozen Calamares3.4.3 public API.
#include <viewpages/ViewStep.h>
#include <utils/PluginFactory.h>
#include <memory>
#include <QByteArray>
#include <QVariantMap>

class QWidget;
class QComboBox;
class QLineEdit;
class QCheckBox;
class QLabel;
class QPlainTextEdit;
class QProcess;
struct ToddyInstallState;

class ToddyViewStep final : public Calamares::ViewStep
{
    Q_OBJECT
public:
    explicit ToddyViewStep(QObject* parent = nullptr);
    ~ToddyViewStep() override;
    QString prettyName() const override;
    QString prettyStatus() const override;
    QWidget* widget() override;
    bool isNextEnabled() const override;
    bool isBackEnabled() const override;
    bool isAtBeginning() const override { return true; }
    bool isAtEnd() const override { return true; }
    Calamares::JobList jobs() const override;
    void setConfigurationMap(const QVariantMap&) override;
    void onActivate() override;
    void onLeave() override;
    void onCancel() override;
private:
    void invalidateReview();
    void query(const QString& action, const QByteArray& body = {});
    void review();
    void status(const QString& message);
    bool m_finished = false;
    QWidget* m_widget = nullptr;
    QComboBox* m_disk = nullptr;
    QComboBox* m_boot = nullptr;
    QComboBox* m_locale = nullptr;
    QComboBox* m_ai = nullptr;
    QLineEdit* m_user = nullptr;
    QLineEdit* m_host = nullptr;
    QLineEdit* m_timezone = nullptr;
    QLineEdit* m_password = nullptr;
    QLineEdit* m_passwordAgain = nullptr;
    QCheckBox* m_confirm = nullptr;
    QCheckBox* m_docker = nullptr;
    QCheckBox* m_opencode = nullptr;
    QCheckBox* m_vscode = nullptr;
    QLabel* m_status = nullptr;
    QPlainTextEdit* m_review = nullptr;
    QProcess* m_query = nullptr;  // Read-only query only; never the install writer.
    QByteArray m_plan;
    quint64 m_generation = 0;
    std::shared_ptr<ToddyInstallState> m_state;
};

CALAMARES_PLUGIN_FACTORY_DECLARATION(ToddyViewStepFactory)
