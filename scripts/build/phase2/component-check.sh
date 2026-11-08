#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
case ${1:-} in
    qtsvg|qttools-linguist|extra-cmake-modules|kcoreaddons|yaml-cpp) ;;
    *) exit 64 ;;
esac
{
printf 'component=%q\n' "$1"
cat <<'NATIVE'
set -euo pipefail
[[ $(dpkg-query -W -f='${Status}' "$component") == 'install ok installed' ]]
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-native-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
cd "$work"
cat > CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.29)
project(ToddyNativeConsumer LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
CMAKE
case $component in
qtsvg)
    cat >> CMakeLists.txt <<'CMAKE'
find_package(Qt6 6.11.2 REQUIRED COMPONENTS Svg)
add_executable(probe probe.cpp)
target_link_libraries(probe PRIVATE Qt6::Svg)
CMAKE
    cat > probe.cpp <<'CPP'
#include <QSvgRenderer>
#include <QImage>
#include <QPainter>
int main() {
    QSvgRenderer good(QByteArray("<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16'><rect width='16' height='16' fill='#123456'/></svg>"));
    QSvgRenderer bad(QByteArray("<svg>"));
    if (!good.isValid() || bad.isValid()) return 1;
    QImage image(16,16,QImage::Format_ARGB32); image.fill(Qt::transparent);
    QPainter painter(&image); good.render(&painter); painter.end();
    return image.pixelColor(8,8) == QColor("#123456") ? 0 : 2;
}
CPP
    ;;
qttools-linguist)
    lrelease -version | grep -F '6.11.2'
    cat > fixture.ts <<'TS'
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS><TS version="2.1" language="pt_BR"><context><name>Fixture</name>
<message><source>Ready</source><translation>Pronto</translation></message></context></TS>
TS
    lrelease fixture.ts -qm fixture.qm
    cat >> CMakeLists.txt <<'CMAKE'
find_package(Qt6 6.11.2 REQUIRED COMPONENTS Core LinguistTools)
add_executable(probe probe.cpp)
target_link_libraries(probe PRIVATE Qt6::Core)
CMAKE
    cat > probe.cpp <<'CPP'
#include <QCoreApplication>
#include <QTranslator>
int main(int argc,char**argv) {
    QCoreApplication app(argc,argv); QTranslator translator;
    if (!translator.load("fixture.qm")) return 1;
    app.installTranslator(&translator);
    return QCoreApplication::translate("Fixture","Ready") == "Pronto" ? 0 : 2;
}
CPP
    ;;
extra-cmake-modules)
    cat >> CMakeLists.txt <<'CMAKE'
find_package(ECM 6.29.0 REQUIRED NO_MODULE)
set(CMAKE_MODULE_PATH ${ECM_MODULE_PATH})
include(KDEInstallDirs)
if(NOT KDE_INSTALL_LIBDIR STREQUAL "lib")
  message(FATAL_ERROR "Native libdir mismatch")
endif()
CMAKE
    cmake -S . -B build -G Ninja -DBUILD_WITH_QT6=ON
    echo NATIVE_ECM_CONSUMER_PASSED
    exit 0
    ;;
kcoreaddons)
    cat >> CMakeLists.txt <<'CMAKE'
find_package(KF6CoreAddons 6.29.0 REQUIRED)
add_executable(probe probe.cpp)
target_link_libraries(probe PRIVATE KF6::CoreAddons)
CMAKE
    cat > probe.cpp <<'CPP'
#include <KAboutData>
#include <KPluginMetaData>
#include <QJsonObject>
#include <QCoreApplication>
int main(int argc,char**argv) {
    QCoreApplication app(argc,argv);
    KAboutData about("toddy-fixture","Toddy Fixture","1.0");
    QJsonObject plugin{{"Id","toddy-fixture"},{"Name","Fixture"}};
    KPluginMetaData metadata(QJsonObject{{"KPlugin",plugin}},QString());
    return about.componentName()=="toddy-fixture" && metadata.pluginId()=="toddy-fixture" ? 0 : 1;
}
CPP
    ;;
yaml-cpp)
    cat >> CMakeLists.txt <<'CMAKE'
find_package(yaml-cpp 0.9.0 REQUIRED)
add_executable(probe probe.cpp)
target_link_libraries(probe PRIVATE yaml-cpp::yaml-cpp)
CMAKE
    cat > probe.cpp <<'CPP'
#include <yaml-cpp/yaml.h>
int main() {
    const auto data=YAML::Load("fixture: [one, two]\ntarget: no-write\n");
    if(data["fixture"].size()!=2 || data["target"].as<std::string>()!="no-write") return 1;
    try { YAML::Load("[broken"); return 2; } catch(const YAML::ParserException&) {}
    return 0;
}
CPP
    ;;
esac
cmake -S . -B build -G Ninja
cmake --build build --parallel 2
./build/probe
echo "NATIVE_CONSUMER_PASSED $component"
NATIVE
} | chroot_run
