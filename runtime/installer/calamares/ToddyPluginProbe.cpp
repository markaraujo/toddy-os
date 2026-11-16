// Original no-write ABI probe; not Calamares startup/root/display qualification.
#include <QApplication>
#include <QJsonDocument>
#include <QJsonObject>
#include <QPluginLoader>
#include <QWidget>
#include <utils/PluginFactory.h>
#include <viewpages/ViewStep.h>
#include <cstdio>
int main(int argc,char**argv)
{
    QApplication app(argc,argv);
    if (argc!=2 || QString::fromLatin1(qVersion())!=QStringLiteral("6.11.2")) return 64;
    QPluginLoader loader(QString::fromLocal8Bit(argv[1]));
    auto* factory=qobject_cast<CalamaresPluginFactory*>(loader.instance());
    if (!factory) return 65;
    auto* view=factory->create<Calamares::ViewStep>();
    if (!view) return 66;
    view->setConfigurationMap({{QStringLiteral("mode"),QStringLiteral("review")}});
    if (view->isNextEnabled() || !view->widget() || view->isNextEnabled()) return 67;
    // onActivate/jobs/exec are deliberately not called: no broker, password,
    // target query, disk write or production-factory override belongs here.
    const auto value=QJsonObject{{"qt",QString::fromLatin1(qVersion())},
        {"plugin_iid",loader.metaData().value("IID")},{"factory_created",true},
        {"review_requires_confirmation",true},{"disk_writes",false}};
    std::puts(QJsonDocument(value).toJson(QJsonDocument::Compact).constData());
    delete view;
    return 0;
}
