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
    font-size: 16px;
    font-weight: 600;
}

QLabel#summaryTitle {
    color: #9CA3AF;
}

QLabel#summaryValue {
    color: #F9FAFB;
    font-size: 26px;
    font-weight: 700;
}

QLabel#moduleStatus {
    color: #94A3B8;
    padding: 4px;
}

QFrame#contentCard,
QFrame#summaryCard {
    background-color: #182235;
    border: 1px solid #29364B;
    border-radius: 10px;
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
"""
