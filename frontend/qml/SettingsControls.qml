import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// Empty controls for Settings Screen
RowLayout {
    id: settingsControls
    spacing: 10
    
    // Reference to the screen this controls
    property var screen
    
    // Force alignment to left
    Layout.alignment: Qt.AlignLeft
    
    // Add a spacer to prevent stretching
    Item {
        Layout.fillWidth: true
    }
} 