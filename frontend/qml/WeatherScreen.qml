import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: weatherScreen
    
    // Property to tell MainWindow which controls to load
    property string screenControls: "WeatherControls.qml"
    
    Rectangle {
        anchors.fill: parent
        color: "#1a1b26"

        Text {
            text: "Weather Screen Placeholder"
            color: "#a9b1d6"
            anchors.centerIn: parent
        }
    }
}
