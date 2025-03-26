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
                                checked: true
                                onCheckedChanged: {
                                    console.log("Auto Send: " + checked)
                                }
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
