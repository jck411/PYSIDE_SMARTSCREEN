import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

import MyScreens 1.0

Rectangle {
    id: chatScreen
    color: "#1a1b26"
    anchors.fill: parent
    
    // ChatLogic is instantiated here from Python.
    ChatLogic {
        id: chatLogic
        
        onMessageReceived: function(text) {
            // For complete messages
            chatModel.append({"text": text, "isUser": false})
            // Auto-scroll to the bottom
            chatView.positionViewAtEnd()
        }
        
        onMessageChunkReceived: function(text, isFinal) {
            // Check if we have an existing assistant message being streamed
            var lastIndex = chatModel.count - 1
            if (lastIndex >= 0 && !chatModel.get(lastIndex).isUser) {
                // Update with accumulated text from Python side
                chatModel.setProperty(lastIndex, "text", text)
            } else {
                // Create a new message
                chatModel.append({"text": text, "isUser": false})
            }
            
            // If this is the final message, we can do any cleanup or formatting needed
            if (isFinal) {
                console.log("Message stream complete")
            }
            
            // Auto-scroll to the bottom
            chatView.positionViewAtEnd()
        }
        
        onConnectionStatusChanged: function(connected) {
            console.log("Connection changed => " + connected)
        }
        
        onSttStateChanged: function(enabled) {
            console.log("STT => " + enabled)
            sttButton.text = enabled ? "STT On" : "STT Off"
        }
        
        onTtsStateChanged: function(enabled) {
            console.log("TTS => " + enabled)
            ttsButton.text = enabled ? "TTS On" : "TTS Off"
        }
    }
    
    // Wrap the layout inside a transparent Rectangle that defines margins.
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
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 40
                    onClicked: chatLogic.toggleSTT()
                }
                Button {
                    id: ttsButton
                    text: "TTS Off"
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 40
                    onClicked: chatLogic.toggleTTS()
                }
                Button {
                    text: "CLEAR"
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 40
                    onClicked: {
                        chatLogic.clearChat()
                        chatModel.clear()
                    }
                }
                Button {
                    text: "STOP"
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 40
                    onClicked: chatLogic.stopAll()
                }
            }
            
            // The chat display area
            ListView {
                id: chatView
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                
                model: ListModel {
                    id: chatModel
                }
                
                delegate: Rectangle {
                    width: ListView.view ? ListView.view.width : 0
                    color: model.isUser ? "#3b4261" : "transparent"
                    radius: 8
                    height: contentLabel.paintedHeight + 16
                    
                    Text {
                        id: contentLabel
                        text: model.text
                        wrapMode: Text.Wrap
                        color: "#a9b1d6"
                        anchors.margins: 8
                        anchors.fill: parent
                    }
                }
                
                // Auto-scroll behavior
                onContentHeightChanged: {
                    chatView.positionViewAtEnd()
                }
            }
            
            RowLayout {
                spacing: 8
                TextField {
                    id: inputField
                    placeholderText: "Type your message..."
                    Layout.fillWidth: true
                    
                    Keys.onPressed: function(event) {
                        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                            sendButton.clicked()
                            event.accepted = true
                        }
                    }
                }
                Button {
                    id: sendButton
                    text: "Send"
                    Layout.preferredWidth: 80
                    onClicked: {
                        let userText = inputField.text.trim()
                        if (userText.length > 0) {
                            chatModel.append({ "text": userText, "isUser": true })
                            inputField.text = ""
                            chatLogic.sendMessage(userText)
                            chatView.positionViewAtEnd()
                        }
                    }
                }
            }
        }
    }
}
