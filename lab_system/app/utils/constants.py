APP_NAME = 'نظام إدارة الاستلام المختبري'
APP_ORG = 'Iraqi Health Laboratory Directorate'
ROLES = ('Admin', 'Supervisor', 'User', 'Auditor')
DEFAULT_WINDOW_SIZE = (1280, 800)
THEME = {
    'bg': '#F5F7FA',
    'panel': '#FFFFFF',
    'primary': '#0F4C81',
    'secondary': '#1F6FB2',
    'success': '#2E7D32',
    'warning': '#ED6C02',
    'error': '#D32F2F',
    'text': '#1F2937',
    'muted': '#6B7280',
    'sidebar_bg': '#0F172A',
    'sidebar_hover': '#1E293B',
    'sidebar_active': '#1E3A5F',
    'sidebar_text': '#94A3B8',
    'sidebar_active_text': '#FFFFFF',
    'border': '#E2E8F0',
    'header_bg': '#F8FAFC',
    'table_alt': '#F8FAFC',
}

TABLE_STYLE = f"""
    QTableWidget {{
        border: 1px solid {THEME['border']};
        border-radius: 6px;
        gridline-color: {THEME['border']};
        selection-background-color: #DBEAFE;
        selection-color: {THEME['sidebar_active']};
        outline: none;
    }}
    QTableWidget::item:hover {{
        background-color: #F1F5F9;
    }}
    QTableWidget::item:selected {{
        background-color: #DBEAFE;
        color: {THEME['sidebar_active']};
    }}
    QHeaderView::section {{
        background-color: {THEME['header_bg']};
        color: #475569;
        font-weight: 600;
        padding: 8px;
        border: none;
        border-bottom: 2px solid {THEME['border']};
    }}
"""
