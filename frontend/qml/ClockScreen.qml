import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

import MyScreens 1.0

Rectangle {
    id: chatScreen
    color: "#1a1b26"
    anchors.fill: parent

    // Our ChatLogic instance; QML instantiates it from Python.
    ChatLogic {
        id: chatLogic
        onMessageReceived: {
            chatModel.append({"text": message, "isUser": false})
        }
        onConnectionStatusChanged: {
            console.log("Connection changed => " + connected)
        }
        onSttStateChanged: {
            console.log("STT => " + isListening)
            sttButton.text = isListening ? "STT On" : "STT Off"
        }
        onTtsStateChanged: {
            console.log("TTS => " + isEnabled)
            ttsButton.text = isEnabled ? "TTS On" : "TTS Off"
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 8
        Layout.leftMargin: 8
        Layout.rightMargin: 8
        Layout.topMargin: 8
        Layout.bottomMargin: 8

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

        // The chat area
        ListView {
            id: chatView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            model: ListModel {
                id: chatModel
            }

            delegate: Rectangle {
                width: parent.width
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
        }

        RowLayout {
            spacing: 8
            TextField {
                id: inputField
                placeholderText: "Type your message..."
                Layout.fillWidth: true
            }
            Button {
                text: "Send"
                Layout.preferredWidth: 80
                onClicked: {
                    let userText = inputField.text.trim()
                    if (userText.length > 0) {
                        chatModel.append({ "text": userText, "isUser": true })
                        inputField.text = ""
                        chatLogic.sendMessage(userText)
                    }
                }
            }
        }
    }
}
