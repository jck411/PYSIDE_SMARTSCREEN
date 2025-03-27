import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0
import MyScreens 1.0
import MySettings 1.0

Item {
    id: settingsScreen
    property string title: "Settings"
    
    // Empty property for controls to maintain pattern with other screens
    // No controls needed for now, but we'll keep the pattern
    property string screenControls: "SettingsControls.qml"
    
    // Reference to ChatLogic for managing settings
    property ChatLogic chatLogic: ChatLogic {}
    
    // Access the auto-send setting directly from the python properties
    property bool autoSendEnabled: false
    
    // Component loading completed - initialize settings
    Component.onCompleted: {
        initSettings()
    }
    
    // When the component becomes visible, refresh settings from the backend
    onVisibleChanged: {
        if (visible) {
            initSettings()
        }
    }
    
    // Initialize settings from ChatLogic
    function initSettings() {
        try {
            // Get the current auto-send state directly from the chatLogic
            autoSendEnabled = chatLogic.isAutoSendEnabled()
            autoSendSwitch.checked = autoSendEnabled
        } catch (e) {
            console.error("Error initializing settings:", e)
        }
    }
    
    Rectangle {
        anchors.fill: parent
        color: ThemeManager.background_color

        ScrollView {
            anchors.fill: parent
            anchors.margins: 16
            clip: true
            
            ColumnLayout {
                width: settingsScreen.width - 32
                spacing: 16
                
                // STT Settings section
                Rectangle {
                    Layout.fillWidth: true
                    height: sttLayout.height + 32
                    color: ThemeManager.input_background_color
                    radius: 8
                    
                    ColumnLayout {
                        id: sttLayout
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        
                        Text {
                            text: "STT Settings"
                            font.pixelSize: 16
                            font.bold: true
                            color: ThemeManager.text_primary_color
                        }
                        
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 16
                            
                            Text {
                                text: "Auto Send:"
                                color: ThemeManager.text_primary_color
                            }
                            
                            Switch {
                                id: autoSendSwitch
                                checked: autoSendEnabled
                                onCheckedChanged: {
                                    console.log("Auto Send: " + checked)
                                    chatLogic.setAutoSend(checked)
                                    autoSendEnabled = checked
                                }
                            }
                            
                            Text {
                                text: "(automatically send transcribed text to chat)"
                                font.italic: true
                                font.pixelSize: 12
                                color: ThemeManager.text_secondary_color
                                Layout.fillWidth: true
                            }
                        }
                    }
                }
                
                // TTS Settings section
                Rectangle {
                    Layout.fillWidth: true
                    height: ttsLayout.height + 32
                    color: ThemeManager.input_background_color
                    radius: 8
                    
                    ColumnLayout {
                        id: ttsLayout
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        
                        Text {
                            text: "TTS Settings"
                            font.pixelSize: 16
                            font.bold: true
                            color: ThemeManager.text_primary_color
                        }
                    }
                }
                
                // Spacer at bottom
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    height: 20
                }
            }
        }
    }
}
