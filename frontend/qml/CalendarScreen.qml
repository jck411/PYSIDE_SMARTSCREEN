import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: calendarScreen
    
    // Property to tell MainWindow which controls to load
    property string screenControls: "CalendarControls.qml"
    
    Rectangle {
        anchors.fill: parent
        color: "#1a1b26"

        Text {
            text: "Calendar Screen Placeholder"
            color: "#a9b1d6"
            anchors.centerIn: parent
        }
    }
}
