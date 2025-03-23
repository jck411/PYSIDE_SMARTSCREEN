import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import MyScreens 1.0

Window {
    id: mainWindow
    width: 800
    height: 480
    color: "#1a1b26"
    visible: true
    title: ""
    
    // Property to track current screen
    property var currentScreen: null
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        
        // Simplified top bar with single RowLayout
        Rectangle {
            id: topBar
            height: 50
            color: "#1a1b26"
            Layout.fillWidth: true
            
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 10
                
                // Screen-specific controls
                Loader {
                    id: screenControlsLoader
                    Layout.fillHeight: true
                    Layout.preferredWidth: 500
                    
                    // Handle component loading status
                    onStatusChanged: {
                        if (status === Loader.Ready && item) {
                            item.screen = stackView.currentItem
                        }
                    }
                }
                
                Item { Layout.fillWidth: true } // Spacer
                
                // Navigation buttons
                Button {
                    text: "Chat"
                    onClicked: stackView.replace("ChatScreen.qml")
                    Layout.preferredWidth: 100
                    Layout.preferredHeight: 36
                }
                
                Button {
                    text: "Weather"
                    onClicked: stackView.replace("WeatherScreen.qml")
                    Layout.preferredWidth: 100
                    Layout.preferredHeight: 36
                }
                
                Button {
                    text: "Calendar"
                    onClicked: stackView.replace("CalendarScreen.qml")
                    Layout.preferredWidth: 100
                    Layout.preferredHeight: 36
                }
                
                Button {
                    text: "Clock"
                    onClicked: stackView.replace("ClockScreen.qml")
                    Layout.preferredWidth: 100
                    Layout.preferredHeight: 36
                }
                
                Button {
                    text: "Photos"
                    onClicked: stackView.replace("PhotoScreen.qml")
                    Layout.preferredWidth: 100
                    Layout.preferredHeight: 36
                }
            }
        }
        
        StackView {
            id: stackView
            Layout.fillWidth: true
            Layout.fillHeight: true
            initialItem: "ChatScreen.qml"
            
            onCurrentItemChanged: {
                currentScreen = currentItem
                
                // Only load controls after current item is fully loaded
                if (currentItem && currentItem.screenControls) {
                    // First clear the old component
                    screenControlsLoader.source = ""
                    // Then load the new one
                    screenControlsLoader.source = currentItem.screenControls
                }
            }
        }
    }
}
