import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import MyScreens 1.0

Window {
    id: mainWindow
    width: 800
    height: 480
    color: "#333333"
    visible: true
    title: "Smart Screen"
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        
        Rectangle {
            id: topBar
            height: 50
            color: "#444444"
            Layout.fillWidth: true
            
            RowLayout {
                anchors.fill: parent
                spacing: 10
                
                Text {
                    text: "Smart Screen"
                    color: "white"
                    verticalAlignment: Text.AlignVCenter
                    font.bold: true
                    Layout.margins: 10
                }
                
                Rectangle { color: "transparent"; Layout.fillWidth: true }
                
                Button {
                    text: "Chat"
                    onClicked: stackView.replace("ChatScreen.qml")
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 40
                }
                
                Button {
                    text: "Weather"
                    onClicked: stackView.replace("WeatherScreen.qml")
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 40
                }
                
                Button {
                    text: "Calendar"
                    onClicked: stackView.replace("CalendarScreen.qml")
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 40
                }
                
                Button {
                    text: "Clock"
                    onClicked: stackView.replace("ClockScreen.qml")
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 40
                }
                
                Button {
                    text: "Photos"
                    onClicked: stackView.replace("PhotoScreen.qml")
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 40
                }
            }
        }
        
        StackView {
            id: stackView
            Layout.fillWidth: true
            Layout.fillHeight: true
            // Since MainWindow.qml and ChatScreen.qml are in the same folder,
            // we use just the file name.
            initialItem: "ChatScreen.qml"
        }
    }
}
