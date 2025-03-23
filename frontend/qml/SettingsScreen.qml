import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import MyTheme 1.0

Item {
    id: settingsScreen
    property string title: "Settings"
    
    // Empty property for controls to maintain pattern with other screens
    // No controls needed for now, but we'll keep the pattern
    property string screenControls: "SettingsControls.qml"
    
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
                
                // Header
                Rectangle {
                    Layout.fillWidth: true
                    height: 50
                    color: ThemeManager.input_background_color
                    radius: 8
                    
                    Text {
                        anchors.centerIn: parent
                        text: "Application Settings"
                        font.pixelSize: 20
                        font.bold: true
                        color: ThemeManager.text_primary_color
                    }
                }
                
                // Theme section
                Rectangle {
                    Layout.fillWidth: true
                    height: themeLayout.height + 32
                    color: ThemeManager.input_background_color
                    radius: 8
                    
                    ColumnLayout {
                        id: themeLayout
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        
                        Text {
                            text: "Theme Settings"
                            font.pixelSize: 16
                            font.bold: true
                            color: ThemeManager.text_primary_color
                        }
                        
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 16
                            
                            Text {
                                text: "Dark Mode:"
                                color: ThemeManager.text_primary_color
                            }
                            
                            Switch {
                                checked: true
                                onCheckedChanged: {
                                    console.log("Dark mode: " + checked)
                                }
                            }
                        }
                    }
                }
                
                // Audio section
                Rectangle {
                    Layout.fillWidth: true
                    height: audioLayout.height + 32
                    color: ThemeManager.input_background_color
                    radius: 8
                    
                    ColumnLayout {
                        id: audioLayout
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        
                        Text {
                            text: "Audio Settings"
                            font.pixelSize: 16
                            font.bold: true
                            color: ThemeManager.text_primary_color
                        }
                        
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 16
                            
                            Text {
                                text: "TTS Volume:"
                                color: ThemeManager.text_primary_color
                            }
                            
                            Slider {
                                id: ttsVolumeSlider
                                Layout.fillWidth: true
                                from: 0
                                to: 100
                                value: 80
                                onValueChanged: {
                                    console.log("TTS volume: " + value)
                                }
                            }
                        }
                        
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 16
                            
                            Text {
                                text: "STT Sensitivity:"
                                color: ThemeManager.text_primary_color
                            }
                            
                            Slider {
                                id: sttSensitivitySlider
                                Layout.fillWidth: true
                                from: 0
                                to: 100
                                value: 70
                                onValueChanged: {
                                    console.log("STT sensitivity: " + value)
                                }
                            }
                        }
                    }
                }
                
                // Other settings
                Rectangle {
                    Layout.fillWidth: true
                    height: otherLayout.height + 32
                    color: ThemeManager.input_background_color
                    radius: 8
                    
                    ColumnLayout {
                        id: otherLayout
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        
                        Text {
                            text: "Display Settings"
                            font.pixelSize: 16
                            font.bold: true
                            color: ThemeManager.text_primary_color
                        }
                        
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 16
                            
                            Text {
                                text: "Screen Brightness:"
                                color: ThemeManager.text_primary_color
                            }
                            
                            Slider {
                                id: brightnessSlider
                                Layout.fillWidth: true
                                from: 0
                                to: 100
                                value: 100
                                onValueChanged: {
                                    console.log("Brightness: " + value)
                                }
                            }
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
