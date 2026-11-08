#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(pkg-config --modversion Qt6Core Qt6Widgets Qt6DBus Qt6Network Qt6Concurrent | sort -u) == 6.11.2 ]]
[[ $(dpkg-query -W -f='${Status}' qtbase) == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-qt-check.XXXXXX)
trap 'rm -rf "$work"' EXIT
cat > "$work/probe.cpp" <<'CPP'
#include <QApplication>
#include <QPushButton>
#include <QVBoxLayout>
#include <QImage>
#include <QPainter>
#include <QCryptographicHash>
#include <QSslSocket>
#include <QDBusConnection>
#include <QtConcurrent>
#include <iostream>
int main(int argc, char **argv) {
    QApplication app(argc, argv);
    if (QGuiApplication::platformName() != "offscreen") return 1;
    if (!QSslSocket::supportsSsl()) return 2;
    if (!QDBusConnection::sessionBus().isConnected()) return 3;
    QWidget window;
    auto *layout = new QVBoxLayout(&window);
    auto *button = new QPushButton("No-write fixture");
    layout->addWidget(button);
    bool clicked = false;
    QObject::connect(button, &QPushButton::clicked, [&]{ clicked = true; });
    window.resize(640, 480); window.show(); app.processEvents();
    button->click();
    QImage image(window.size(), QImage::Format_ARGB32);
    image.fill(Qt::transparent); window.render(&image);
    auto future = QtConcurrent::run([]{ return 42; });
    future.waitForFinished();
    if (!clicked || future.result() != 42 || image.isNull()) return 4;
    auto hash = QCryptographicHash::hash(QByteArray("toddy"), QCryptographicHash::Sha256);
    if (hash.size() != 32) return 5;
    std::cout << "NATIVE_QT_OFFSCREEN_WIDGET_TLS_DBUS_CONCURRENT_PASSED\n";
}
CPP
c++ -std=c++17 "$work/probe.cpp" $(pkg-config --cflags --libs Qt6Widgets Qt6DBus Qt6Network Qt6Concurrent) -o "$work/probe"
QT_QPA_PLATFORM=offscreen dbus-run-session -- "$work/probe"
NATIVE
