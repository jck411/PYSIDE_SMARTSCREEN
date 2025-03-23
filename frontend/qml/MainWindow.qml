import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import MyScreens 1.0
import MyTheme 1.0  // Import our ThemeManager

Window {
    id: mainWindow
    width: 800
    height: 480
    color: ThemeManager.background_color
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
            color: ThemeManager.background_color
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
                    Layout.preferredWidth: 200
                    
                    // Handle component loading status
                    onStatusChanged: {
                        if (status === Loader.Ready && item) {
                            item.screen = stackView.currentItem
                        }
                    }
                }
                
                Item { 
                    Layout.fillWidth: true 
                    Layout.preferredWidth: 50
                } // Spacer
                
                // Navigation icons
                Button {
                    id: chatButton
                    Layout.preferredWidth: 50
                    Layout.preferredHeight: 40
                    background: Rectangle {
                        color: "transparent"
                        border.color: stackView.currentItem.toString().includes("ChatScreen") ? ThemeManager.button_primary_color : "transparent"
                        border.width: 2
                        radius: 5
                    }
                    onClicked: stackView.replace("ChatScreen.qml")
                    
                    Image {
                        anchors.centerIn: parent
                        source: "../icons/chat.svg"
                        width: 24
                        height: 24
                        sourceSize.width: 24
                        sourceSize.height: 24
                    }
                }
                
                Button {
                    id: weatherButton
                    Layout.preferredWidth: 50
                    Layout.preferredHeight: 40
                    background: Rectangle {
                        color: "transparent"
                        border.color: stackView.currentItem.toString().includes("WeatherScreen") ? ThemeManager.button_primary_color : "transparent"
                        border.width: 2
                        radius: 5
                    }
                    onClicked: stackView.replace("WeatherScreen.qml")
                    
                    Image {
                        anchors.centerIn: parent
                        source: "../icons/weather.svg"
                        width: 24
                        height: 24
                        sourceSize.width: 24
                        sourceSize.height: 24
                    }
                }
                
                Button {
                    id: calendarButton
                    Layout.preferredWidth: 50
                    Layout.preferredHeight: 40
                    background: Rectangle {
                        color: "transparent"
                        border.color: stackView.currentItem.toString().includes("CalendarScreen") ? ThemeManager.button_primary_color : "transparent"
                        border.width: 2
                        radius: 5
                    }
                    onClicked: stackView.replace("CalendarScreen.qml")
                    
                    Image {
                        anchors.centerIn: parent
                        source: "../icons/calendar.svg"
                        width: 24
                        height: 24
                        sourceSize.width: 24
                        sourceSize.height: 24
                    }
                }
                
                Button {
                    id: clockButton
                    Layout.preferredWidth: 50
                    Layout.preferredHeight: 40
                    background: Rectangle {
                        color: "transparent"
                        border.color: stackView.currentItem.toString().includes("ClockScreen") ? ThemeManager.button_primary_color : "transparent"
                        border.width: 2
                        radius: 5
                    }
                    onClicked: stackView.replace("ClockScreen.qml")
                    
                    Image {
                        anchors.centerIn: parent
                        source: "../icons/clock.svg"
                        width: 24
                        height: 24
                        sourceSize.width: 24
                        sourceSize.height: 24
                    }
                }
                
                Button {
                    id: photosButton
                    Layout.preferredWidth: 50
                    Layout.preferredHeight: 40
                    background: Rectangle {
                        color: "transparent"
                        border.color: stackView.currentItem.toString().includes("PhotoScreen") ? ThemeManager.button_primary_color : "transparent"
                        border.width: 2
                        radius: 5
                    }
                    onClicked: stackView.replace("PhotoScreen.qml")
                    
                    Image {
                        anchors.centerIn: parent
                        source: "../icons/photos.svg"
                        width: 24
                        height: 24
                        sourceSize.width: 24
                        sourceSize.height: 24
                    }
                }
                
                Button {
                    id: themeToggleButton
                    Layout.preferredWidth: 50
                    Layout.preferredHeight: 40
                    background: Rectangle {
                        color: "transparent"
                        radius: 5
                    }
                    onClicked: ThemeManager.toggle_theme()
                    
                    Image {
                        anchors.centerIn: parent
                        source: ThemeManager.is_dark_mode ? "../icons/light_mode.svg" : "../icons/dark_mode.svg"
                        width: 24
                        height: 24
                        sourceSize.width: 24
                        sourceSize.height: 24
                    }
                    
                    ToolTip.visible: hovered
                    ToolTip.text: ThemeManager.is_dark_mode ? "Switch to Light Mode" : "Switch to Dark Mode"
                }
                
                Button {
                    id: settingsButton
                    Layout.preferredWidth: 50
                    Layout.preferredHeight: 40
                    background: Rectangle {
                        color: "transparent"
                        border.color: stackView.currentItem.toString().includes("SettingsScreen") ? ThemeManager.button_primary_color : "transparent"
                        border.width: 2
                        radius: 5
                    }
                    onClicked: stackView.replace("SettingsScreen.qml")
                    
                    Image {
                        anchors.centerIn: parent
                        source: "../icons/settings.svg"
                        width: 24
                        height: 24
                        sourceSize.width: 24
                        sourceSize.height: 24
                    }
                    
                    ToolTip.visible: hovered
                    ToolTip.text: "Settings"
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
