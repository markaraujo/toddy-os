// B01 native no-write fixture. Link/run the real Calamares Python Job API.
#include "GlobalStorage.h"
#include "JobQueue.h"
#include "pybind11/PythonJob.h"
#include <QCoreApplication>
#include <QJsonDocument>
#include <QJsonObject>
#include <QVariantMap>
#include <iostream>
#include <memory>

int main(int argc, char **argv) {
    QCoreApplication application(argc, argv);
    Calamares::JobQueue queue;
    QVariantMap config{{"schema_version", 1},
                       {"target_serial", "TODDY-INSTALL-FIXTURE"},
                       {"boot_mode", "uefi"}, {"ai_choice", "later"},
                       {"extras", QStringList{"docker", "opencode"}}};
    std::unique_ptr<Calamares::Job> job(new Calamares::Python::Job(
        "target_plan_fixture.py", "/src/toddy-fixtures", config));
    auto result = job->exec();
    if (!result.succeeded()) {
        std::cerr << result.message().toStdString() << ": " << result.details().toStdString() << "\n";
        return 1;
    }
    const auto json = queue.globalStorage()->value("toddyFixturePlanJson").toString().toUtf8();
    if (json.size() > 32768) return 2;
    const auto document = QJsonDocument::fromJson(json);
    if (!document.isObject() || !document.object().value("offline_desktop").isBool() ||
        !document.object().value("mandatory_agent_backend").isBool() ||
        !document.object().value("credentials_in_installer").isBool()) return 2;
    const auto plan = document.toVariant().toMap();
    if (plan.value("scope").toString() != "synthetic-no-write" ||
        plan.value("mandatory_agent_backend").toBool() ||
        plan.value("credentials_in_installer").toBool() ||
        plan.value("negative_cases").toInt() != 9 ||
        plan.value("extras_deferred").toStringList() != QStringList{"docker", "opencode"}) return 2;
    std::cout << QJsonDocument::fromVariant(plan).toJson(QJsonDocument::Compact).constData() << "\n";
    std::cout << "NATIVE_CALAMARES_PYTHON_JOB_TARGET_PLAN_PASSED\n";
}
