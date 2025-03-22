import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

import MyScreens 1.0

Item {
    id: chatScreen
    property string title: "Chat Interface"
    
    Rectangle {
        anchors.fill: parent
        color: "#15161e"

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
            
            onSttStateChanged: function(enabled) {
                console.log("STT => " + enabled)
                sttButton.text = enabled ? "STT On" : "STT Off"
                sttButton.isListening = enabled
            }
            
            onTtsStateChanged: function(enabled) {
                console.log("TTS => " + enabled)
                ttsButton.text = enabled ? "TTS On" : "TTS Off"
                ttsButton.isEnabled = enabled
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
                
                RowLayout {
                    spacing: 8
                    Button {
                        id: sttButton
                        text: "STT Off"
                        property bool isListening: false
                        Layout.preferredWidth: 120
                        Layout.preferredHeight: 40
                        onClicked: {
                            isListening = !isListening
                            text = isListening ? "STT On" : "STT Off"
                            chatLogic.toggleSTT()
                        }
                    }
                    Button {
                        id: ttsButton
                        text: "TTS Off"
                        property bool isEnabled: false
                        Layout.preferredWidth: 120
                        Layout.preferredHeight: 40
                        onClicked: {
                            isEnabled = !isEnabled
                            text = isEnabled ? "TTS On" : "TTS Off"
                            chatLogic.toggleTTS()
                        }
                    }
                    Button {
                        id: clearButton
                        text: "CLEAR"
                        Layout.preferredWidth: 120
                        Layout.preferredHeight: 40
                        onClicked: {
                            chatLogic.clearChat()
                            chatModel.clear()
                        }
                    }
                    Button {
                        id: stopButton
                        text: "STOP"
                        Layout.preferredWidth: 120
                        Layout.preferredHeight: 40
                        onClicked: chatLogic.stopAll()
                    }
                }
                
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
                        color: model.isUser ? "#3b4261" : "#24283b"
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
                            color: "#a9b1d6"
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
                            color: "#24283b"
                            radius: 4
                            border.width: 1
                            border.color: "#5a6181"
                        }
                        
                        color: "#a9b1d6"
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
                        text: "Send"
                        Layout.preferredWidth: 80
                        Layout.preferredHeight: 40
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
