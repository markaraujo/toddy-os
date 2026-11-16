// Native staged/installed consumer, never a compositor or disk-install proof.
#include <QApplication>
#include <QPushButton>
#include <QImage>
#include <QPainter>
#include <QPluginLoader>
#include <QJsonArray>
#include <QJsonObject>
#include <QDBusConnection>
#include <QSslSocket>
#include <QtConcurrent>
#include <QSvgRenderer>
#include <QtGui/qtgui-config.h>
#include <iostream>
static_assert(QT_FEATURE_wayland == 1 && QT_FEATURE_waylandscanner == 1 && QT_FEATURE_xkbcommon == 1);
int main(int argc, char** argv) {
    QApplication app(argc, argv);
    if (QString::fromLatin1(qVersion()) != QStringLiteral("6.11.2") || QGuiApplication::platformName() != "offscreen") return 1;
    if (!QSslSocket::supportsSsl() || !QDBusConnection::sessionBus().isConnected()) return 2;
#ifdef TODDY_STAGED_QT
    const QString prefix = QStringLiteral("/stage/usr");
#else
    const QString prefix = QStringLiteral("/usr");
#endif
    QPluginLoader plugin(prefix + "/plugins/platforms/libqwayland.so");
    const auto keys = plugin.metaData().value("MetaData").toObject().value("Keys").toArray();
    if (!keys.contains("wayland")) return 3; // Metadata only, no Wayland session here.
    QPushButton button(QString::fromUtf8("Toddy · instalação · ação"));
    bool clicked = false;
    QObject::connect(&button, &QPushButton::clicked, [&] { clicked = true; });
    button.resize(640, 320); button.show(); app.processEvents(); button.click();
    QImage image(button.size(), QImage::Format_ARGB32); image.fill(Qt::transparent);
    button.render(&image);
    QSvgRenderer svg(QByteArray("<svg xmlns='http://www.w3.org/2000/svg' width='20' height='20'><rect width='20' height='20' fill='navy'/></svg>"));
    if (!svg.isValid()) return 4;
    QPainter painter(&image); svg.render(&painter); painter.end();
    auto future = QtConcurrent::run([] { return 42; }); future.waitForFinished();
    if (!clicked || image.isNull() || future.result() != 42) return 5;
    std::cout << "QT6112_WIDGET_TLS_DBUS_CONCURRENT_EXISTING_SVG_WAYLAND_METADATA_PASSED\n";
}
