"""CyberLab Desktop Suite görsel tema ayarları."""

DARK_STYLESHEET = """
QMainWindow,
QWidget {
    background-color: #111827;
    color: #E5E7EB;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

QFrame#sidebar {
    background-color: #0B1220;
    border-right: 1px solid #253044;
}

QLabel#brandTitle {
    font-size: 19px;
    font-weight: 700;
    color: #F9FAFB;
}

QLabel#brandSubtitle {
    color: #22D3A6;
    font-size: 11px;
}

QLabel#pageTitle {
    font-size: 27px;
    font-weight: 700;
    color: #F9FAFB;
}

QLabel#pageDescription {
    color: #9CA3AF;
    font-size: 14px;
}

QLabel#sectionTitle {
    color: #F8FAFC;
    font-size: 15px;
    font-weight: 700;
    padding-bottom: 6px;
}

QLabel#summaryIcon {
    color: #22D3A6;
    font-size: 18px;
    font-weight: 700;

    background-color: transparent;
    border: 1px solid #2D6B61;
    border-radius: 8px;

    padding: 4px 7px;
}

QLabel#summaryTitle {
    color: #CBD5E1;
    font-size: 13px;
    font-weight: 600;
}

QLabel#summaryValue {
    color: #F8FAFC;
    font-size: 30px;
    font-weight: 700;
}

QLabel#moduleStatus {
    color: #94A3B8;
    padding: 4px;
}

QFrame#contentCard {
    background-color: transparent;
    border: 1px solid #34445D;
    border-radius: 12px;
}

QFrame#summaryCard {
    background-color: transparent;
    border: 1px solid #34445D;
    border-radius: 12px;
}

QFrame#summaryCard:hover {
    background-color: rgba(34, 211, 166, 0.04);
    border-color: #22D3A6;
}

QPushButton {
    background-color: #263449;
    border: 1px solid #34445D;
    border-radius: 7px;
    padding: 9px 14px;
    color: #F9FAFB;
}

QPushButton:hover {
    background-color: #30415A;
}

QPushButton:disabled {
    background-color: #1C2738;
    color: #64748B;
}

QPushButton#primaryButton {
    background-color: #0F9F79;
    border-color: #15B88B;
    font-weight: 600;
}

QPushButton#navigationButton {
    text-align: left;
    padding: 11px 14px;
    background-color: transparent;
    border: none;
}

QPushButton#navigationButton:hover {
    background-color: #172338;
}

QPushButton#navigationButton:checked {
    background-color: #183E3A;
    color: #4ADEB6;
    border-left: 3px solid #22D3A6;
}

QLineEdit {
    background-color: #101827;
    border: 1px solid #34445D;
    border-radius: 7px;
    padding: 9px;
}

QTableWidget {
    background-color: #101827;
    alternate-background-color: #141F31;
    border: 1px solid #29364B;
    border-radius: 7px;
    gridline-color: #29364B;
}

QHeaderView::section {
    background-color: #1B293D;
    color: #CBD5E1;
    border: none;
    border-bottom: 1px solid #34445D;
    padding: 9px;
    font-weight: 600;
}

QStatusBar {
    background-color: #0B1220;
    color: #94A3B8;
}

QFrame#splashContainer {
    background-color: #0B1220;
    border: 1px solid #29364B;
    border-radius: 18px;
}

QLabel#splashBrand {
    color: #F9FAFB;
    letter-spacing: 4px;
}

QLabel#splashProduct {
    color: #CBD5E1;
    font-size: 17px;
    font-weight: 600;
}

QLabel#splashSlogan {
    color: #22D3A6;
    font-size: 14px;
}

QLabel#splashVersion {
    color: #64748B;
    font-size: 12px;
}

QLabel#splashStatus {
    color: #94A3B8;
    font-size: 12px;
}

QProgressBar#splashProgress {
    background-color: #182235;
    border: none;
    border-radius: 4px;
}

QProgressBar#splashProgress::chunk {
    background-color: #22D3A6;
    border-radius: 4px;
}

QProgressBar#analysisProgress {
    background-color: #101827;
    border: 1px solid #34445D;
    border-radius: 8px;
    color: #E5E7EB;
    font-size: 11px;
    font-weight: 600;
    text-align: center;
}

QProgressBar#analysisProgress::chunk {
    background-color: #0F9F79;
    border-radius: 7px;
}

QPlainTextEdit#analysisLog {
    background-color: #0B1220;
    border: 1px solid #29364B;
    border-radius: 8px;
    padding: 8px;

    color: #CBD5E1;

    font-family: Consolas, "Courier New", monospace;
    font-size: 12px;

    selection-background-color: #164E63;
}

QSplitter#resultsSplitter::handle {
    background-color: transparent;
    width: 8px;
}

QSplitter#resultsSplitter::handle:hover {
    background-color: #22D3A6;
    border-radius: 3px;
}

QLabel#detailTitle {
    color: #94A3B8;
    font-size: 12px;
    font-weight: 600;
}

QLabel#detailValue {
    color: #F8FAFC;
    font-size: 13px;
    font-weight: 600;
}

QSplitter#clientsSplitter::handle {
    background-color: transparent;
    width: 8px;
}

QSplitter#clientsSplitter::handle:hover {
    background-color: #22D3A6;
    border-radius: 3px;
}

QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 4px;
}

QScrollBar::handle:vertical {
    background: #34445D;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #22D3A6;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
