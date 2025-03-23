import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

RowLayout {
    id: clockControls
    spacing: 8
    
    property var screen
    
    // Empty layout to maintain structure
    Item {
        Layout.fillWidth: true
    }
} 