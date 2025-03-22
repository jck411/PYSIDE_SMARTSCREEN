import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

import MyScreens 1.0

Rectangle {
    id: chatScreen
    color: "#15161e"  // Slightly darker for better contrast
    anchors.fill: parent
    
    // ChatLogic is instantiated here from Python.
    ChatLogic {
        id: chatLogic
        
        onMessageReceived: function(text) {
            // For complete messages
            chatModel.append({"text": text, "isUser": false})
            // Auto-scroll to the bottom only if autoScroll is true
            if (chatView.autoScroll) {
                chatView.positionViewAtEnd()
            }
        }
        
        onMessageChunkReceived: function(text, isFinal) {
            // Handle streaming response, exactly like client.py
            var lastIndex = chatModel.count - 1
            if (lastIndex >= 0 && !chatModel.get(lastIndex).isUser) {
                // Update existing bubble with accumulated text
                chatModel.setProperty(lastIndex, "text", text)
            } else {
                // Create a new message bubble
                chatModel.append({"text": text, "isUser": false})
            }
            
            // If this is the final message in the stream, we're finished
            if (isFinal) {
                console.log("Message stream complete")
            }
            
            // Auto-scroll to the bottom only if autoScroll is true
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
            ttsButton.enabled = enabled
        }
        
        onSttInputTextReceived: function(text) {
            inputField.text = text
        }
    }
    
    // For window title
    property string title: "Chat Interface"
    
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
                    property bool isListening: false
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 40
                    onClicked: chatLogic.toggleSTT()
                }
                Button {
                    id: ttsButton
                    text: "TTS Off"
                    property bool enabled: false
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 40
                    onClicked: chatLogic.toggleTTS()
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
            
            // The chat display area
            ListView {
                id: chatView
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 8
                
                model: ListModel {
                    id: chatModel
                }
                
                delegate: Rectangle {
                    width: ListView.view ? ListView.view.width - 16 : 0
                    color: model.isUser ? "#3b4261" : "#24283b"
                    radius: 8
                    height: contentLabel.paintedHeight + 16
                    
                    // Position messages on opposite sides like in a standard chat app
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
                
                // Add property to control auto-scrolling
                property bool autoScroll: true
                
                // Add mouse wheel handler to detect user scrolling
                MouseArea {
                    anchors.fill: parent
                    onWheel: function(wheel) {
                        // When user scrolls manually, disable auto-scroll
                        if (wheel.angleDelta.y < 0 && chatView.atYEnd) {
                            // Scrolling down at bottom - keep auto-scroll
                            chatView.autoScroll = true;
                        } else if (wheel.angleDelta.y > 0) {
                            // Scrolling up - disable auto-scroll
                            chatView.autoScroll = false;
                        }
                        // Don't consume the wheel event, let it pass to the ListView
                        wheel.accepted = false;
                    }
                    
                    // Handle click to allow message selection but not block the ListView
                    onClicked: mouse.accepted = false
                    onPressed: mouse.accepted = false
                    onReleased: mouse.accepted = false
                }
            }
            
            RowLayout {
                spacing: 8
                TextField {
                    id: inputField
                    placeholderText: "Type your message..."
                    Layout.fillWidth: true
                    
                    // Style similar to client.py
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
                            // When sending a message, always re-enable auto-scroll
                            chatView.autoScroll = true
                            chatView.positionViewAtEnd()
                        }
                    }
                }
            }
        }
    }
    
    // When user clicks anywhere in the chat, try to focus the input field
    MouseArea {
        anchors.fill: parent
        z: -1 // Behind everything else
        onClicked: {
            inputField.forceActiveFocus()
        }
    }
}
