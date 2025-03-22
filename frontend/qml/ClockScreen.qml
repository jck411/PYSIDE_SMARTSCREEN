import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: clockScreen
    
    Rectangle {
        anchors.fill: parent
        color: "#1a1b26"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 10

            Text {
                id: timeText
                Layout.alignment: Qt.AlignCenter
                color: "#a9b1d6"
                font.pixelSize: 72
                font.bold: true
                text: "00:00:00"
            }

            Text {
                id: dateText
                Layout.alignment: Qt.AlignCenter
                color: "#a9b1d6"
                font.pixelSize: 28
                text: "January 1, 2023"
            }

            // Spacer
            Item {
                Layout.fillHeight: true
            }
        }

        Timer {
            interval: 1000
            running: true
            repeat: true
            triggeredOnStart: true
            onTriggered: {
                var date = new Date()
                timeText.text = date.toLocaleTimeString(Qt.locale(), "hh:mm:ss")
                dateText.text = date.toLocaleDateString(Qt.locale(), "MMMM d, yyyy")
            }
        }
    }
}
