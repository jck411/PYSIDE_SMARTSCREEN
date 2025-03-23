import QtQuick 2.15
import QtQuick.Controls 2.15
import MyTheme 1.0

Item {
    id: weatherScreen
    
    // Property to tell MainWindow which controls to load
    property string screenControls: "WeatherControls.qml"
    
    Rectangle {
        anchors.fill: parent
        color: ThemeManager.background_color

        Text {
            text: "Weather Screen Placeholder"
            color: ThemeManager.text_primary_color
            anchors.centerIn: parent
        }
    }
}
