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
                        if (status === Loader.Ready && item && currentScreen) {
                            item.screen = currentScreen
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
                        border.color: screenContainer.currentScreenName === "ChatScreen" ? ThemeManager.button_primary_color : "transparent"
                        border.width: 2
                        radius: 5
                    }
                    onClicked: screenContainer.currentScreenName = "ChatScreen"
                    
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
                        border.color: screenContainer.currentScreenName === "WeatherScreen" ? ThemeManager.button_primary_color : "transparent"
                        border.width: 2
                        radius: 5
                    }
                    onClicked: screenContainer.currentScreenName = "WeatherScreen"
                    
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
                        border.color: screenContainer.currentScreenName === "CalendarScreen" ? ThemeManager.button_primary_color : "transparent"
                        border.width: 2
                        radius: 5
                    }
                    onClicked: screenContainer.currentScreenName = "CalendarScreen"
                    
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
                        border.color: screenContainer.currentScreenName === "ClockScreen" ? ThemeManager.button_primary_color : "transparent"
                        border.width: 2
                        radius: 5
                    }
                    onClicked: screenContainer.currentScreenName = "ClockScreen"
                    
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
                        border.color: screenContainer.currentScreenName === "PhotoScreen" ? ThemeManager.button_primary_color : "transparent"
                        border.width: 2
                        radius: 5
                    }
                    onClicked: screenContainer.currentScreenName = "PhotoScreen"
                    
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
                        border.color: screenContainer.currentScreenName === "SettingsScreen" ? ThemeManager.button_primary_color : "transparent"
                        border.width: 2
                        radius: 5
                    }
                    onClicked: screenContainer.currentScreenName = "SettingsScreen"
                    
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
        
        // Container for all screens
        Item {
            id: screenContainer
            Layout.fillWidth: true
            Layout.fillHeight: true
            
            // Property to track current screen name
            property string currentScreenName: "ChatScreen"
            
            // Load all screens at startup but keep them hidden
            ChatScreen {
                id: chatScreen
                anchors.fill: parent
                visible: screenContainer.currentScreenName === "ChatScreen"
            }
            
            WeatherScreen {
                id: weatherScreen
                anchors.fill: parent
                visible: screenContainer.currentScreenName === "WeatherScreen"
            }
            
            CalendarScreen {
                id: calendarScreen
                anchors.fill: parent
                visible: screenContainer.currentScreenName === "CalendarScreen"
            }
            
            ClockScreen {
                id: clockScreen
                anchors.fill: parent
                visible: screenContainer.currentScreenName === "ClockScreen"
            }
            
            PhotoScreen {
                id: photoScreen
                anchors.fill: parent
                visible: screenContainer.currentScreenName === "PhotoScreen"
            }
            
            SettingsScreen {
                id: settingsScreen
                anchors.fill: parent
                visible: screenContainer.currentScreenName === "SettingsScreen"
            }
            
            // Update current screen reference and load controls
            onCurrentScreenNameChanged: {
                console.log("Switching to screen:", currentScreenName);
                
                // Update current screen reference
                switch(currentScreenName) {
                    case "ChatScreen":
                        currentScreen = chatScreen;
                        break;
                    case "WeatherScreen":
                        currentScreen = weatherScreen;
                        break;
                    case "CalendarScreen":
                        currentScreen = calendarScreen;
                        break;
                    case "ClockScreen":
                        currentScreen = clockScreen;
                        break;
                    case "PhotoScreen":
                        currentScreen = photoScreen;
                        break;
                    case "SettingsScreen":
                        currentScreen = settingsScreen;
                        break;
                }
                
                // Load screen-specific controls
                if (currentScreen && currentScreen.screenControls) {
                    // First clear the old component
                    screenControlsLoader.source = "";
                    // Then load the new one
                    screenControlsLoader.source = currentScreen.screenControls;
                }
            }
            
            // Initialize with chat screen and load controls
            Component.onCompleted: {
                currentScreen = chatScreen;
                
                // Explicitly load the chat controls on startup
                if (currentScreen && currentScreen.screenControls) {
                    console.log("Loading initial controls:", currentScreen.screenControls);
                    screenControlsLoader.source = currentScreen.screenControls;
                }
            }
        }
    }
}
