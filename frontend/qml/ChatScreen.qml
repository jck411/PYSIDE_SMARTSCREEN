import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

import MyScreens 1.0
import MyTheme 1.0  // Import our ThemeManager

Item {
    id: chatScreen
    property string title: "Chat Interface"
    
    // Properties to expose chat logic and model to controls
    property alias chatLogic: chatLogic
    property alias chatModel: chatModel
    
    // Property to tell MainWindow which controls to load
    property string screenControls: "ChatControls.qml"
    
    Rectangle {
        anchors.fill: parent
        color: ThemeManager.background_color

        ChatLogic {
            id: chatLogic
            
            onMessageReceived: function(text) {
                chatModel.append({"text": text, "isUser": false})
                if (chatView.autoScroll) {
                    chatView.positionViewAtEnd()
                }
            }
            
            onMessageChunkReceived: function(text, isFinal) {
                var lastIndex = chatModel.count - 1
                if (lastIndex >= 0 && !chatModel.get(lastIndex).isUser) {
                    chatModel.setProperty(lastIndex, "text", text)
                } else {
                    chatModel.append({"text": text, "isUser": false})
                }
                
                if (isFinal) {
                    console.log("Message stream complete")
                }
                
                if (chatView.autoScroll) {
                    chatView.positionViewAtEnd()
                }
            }
            
            onConnectionStatusChanged: function(connected) {
                console.log("Connection changed => " + connected)
                chatScreen.title = connected ? "Chat Interface - Connected" : "Chat Interface - Disconnected"
            }
            
            onSttInputTextReceived: function(text) {
                inputField.text = text
            }
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: 8
            color: "transparent"
            
            ColumnLayout {
                anchors.fill: parent
                spacing: 8
                
                ListView {
                    id: chatView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 8
                    property bool autoScroll: true
                    
                    model: ListModel {
                        id: chatModel
                    }
                    
                    delegate: Rectangle {
                        width: ListView.view ? ListView.view.width - 16 : 0
                        color: model.isUser ? ThemeManager.user_bubble_color : ThemeManager.assistant_bubble_color
                        radius: 8
                        height: contentLabel.paintedHeight + 16
                        
                        anchors.right: model.isUser ? parent.right : undefined
                        anchors.left: model.isUser ? undefined : parent.left
                        anchors.rightMargin: model.isUser ? 8 : 0
                        anchors.leftMargin: model.isUser ? 0 : 8
                        
                        Text {
                            id: contentLabel
                            text: model.text
                            wrapMode: Text.Wrap
                            width: parent.width - 16
                            color: ThemeManager.text_primary_color
                            anchors.margins: 8
                            anchors.centerIn: parent
                        }
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        propagateComposedEvents: true
                        
                        onWheel: function(wheel) {
                            if (wheel.angleDelta.y < 0 && chatView.atYEnd) {
                                chatView.autoScroll = true
                            } else if (wheel.angleDelta.y > 0) {
                                chatView.autoScroll = false
                            }
                            wheel.accepted = false
                        }
                    }
                }
                
                RowLayout {
                    spacing: 8
                    TextField {
                        id: inputField
                        placeholderText: "Type your message..."
                        Layout.fillWidth: true
                        
                        background: Rectangle {
                            color: ThemeManager.input_background_color
                            radius: 4
                            border.width: 1
                            border.color: ThemeManager.input_border_color
                        }
                        
                        color: ThemeManager.text_primary_color
                        selectByMouse: true
                        
                        Keys.onPressed: function(event) {
                            if ((event.key === Qt.Key_Return || event.key === Qt.Key_Enter) && 
                                !(event.modifiers & Qt.ShiftModifier)) {
                                sendButton.clicked()
                                event.accepted = true
                            }
                        }
                    }
                    
                    Button {
                        id: sendButton
                        Layout.preferredWidth: 40
                        Layout.preferredHeight: 40
                        background: Rectangle {
                            color: "transparent"
                            radius: 5
                        }
                        onClicked: {
                            let userText = inputField.text.trim()
                            if (userText.length > 0) {
                                chatModel.append({ "text": userText, "isUser": true })
                                inputField.text = ""
                                chatLogic.sendMessage(userText)
                                chatView.autoScroll = true
                                chatView.positionViewAtEnd()
                            }
                        }
                        
                        Image {
                            anchors.centerIn: parent
                            source: "../icons/send.svg"
                            width: 24
                            height: 24
                            sourceSize.width: 24
                            sourceSize.height: 24
                        }
                        
                        ToolTip.visible: hovered
                        ToolTip.text: "Send"
                    }
                }
            }
        }

        MouseArea {
            anchors.fill: parent
            z: -1
            onClicked: {
                inputField.forceActiveFocus()
            }
        }
    }
}
