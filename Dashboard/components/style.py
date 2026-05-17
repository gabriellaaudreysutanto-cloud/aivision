from components.ui import markdown_html


def global_style():
    markdown_html(
        """
        <style>
        :root {
            --font-app: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
            --page-bg: #f5f5f7;
            --page-bg-soft: #fbfbfd;
            --surface: #ffffff;
            --surface-elevated: rgba(255, 255, 255, 0.92);
            --surface-muted: #f9f9fb;
            --separator: rgba(0, 0, 0, 0.10);
            --separator-soft: rgba(0, 0, 0, 0.06);
            --separator-strong: rgba(0, 0, 0, 0.14);
            --text: #1d1d1f;
            --text-secondary: #6e6e73;
            --text-tertiary: #86868b;
            --text-inverse: #ffffff;
            --blue: #0071e3;
            --blue-hover: #0077ed;
            --blue-pressed: #006edb;
            --blue-soft: #f0f7ff;
            --green: #248a3d;
            --green-soft: #f0f9f2;
            --orange: #bf5b00;
            --orange-soft: #fff7ed;
            --red: #d70015;
            --red-soft: #fff2f4;
            --purple: #8e56cf;
            --purple-soft: #f8f1ff;
            --teal: #0071e3;
            --teal-soft: #f0f7ff;
            --amber: #bf5b00;
            --amber-soft: #fff7ed;
            --sky-soft: #f0f7ff;
            --accent-gradient: var(--blue);
            --accent-gradient-hover: var(--blue-hover);
            --radius-sm: 10px;
            --radius-md: 14px;
            --radius-lg: 18px;
            --shadow-rest: 0 1px 2px rgba(0, 0, 0, 0.04), 0 8px 24px rgba(0, 0, 0, 0.05);
            --shadow-hover: 0 2px 4px rgba(0, 0, 0, 0.05), 0 14px 34px rgba(0, 0, 0, 0.08);
            --focus-ring: 0 0 0 4px rgba(0, 113, 227, 0.18);
        }

        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"] {
            background: var(--page-bg);
            color: var(--text);
            font-family: var(--font-app);
        }

        [data-testid="stAppViewContainer"] {
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.72) 0, rgba(245, 245, 247, 0) 260px),
                var(--page-bg);
        }

        .stApp,
        .stApp * {
            box-sizing: border-box;
            font-family: var(--font-app);
            letter-spacing: 0;
            -webkit-font-smoothing: antialiased;
            text-rendering: optimizeLegibility;
        }

        .main .block-container,
        [data-testid="stMain"] .block-container {
            max-width: 1280px;
            padding: 1.85rem 2.2rem 2.4rem;
        }

        [data-testid="stVerticalBlock"] {
            gap: 1rem;
        }

        h1,
        h2,
        h3,
        h4,
        h5,
        h6 {
            color: var(--text);
            font-weight: 650;
            letter-spacing: 0;
        }

        p,
        label,
        span {
            letter-spacing: 0;
        }

        [data-testid="stMarkdownContainer"] p {
            color: inherit;
        }

        label,
        [data-testid="stWidgetLabel"] p {
            color: var(--text) !important;
            font-size: 0.88rem !important;
            font-weight: 590 !important;
        }

        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p {
            color: var(--text-secondary) !important;
            font-size: 0.81rem !important;
        }

        .app-page-header {
            align-items: flex-start;
            background: var(--surface-elevated);
            border: 1px solid var(--separator-soft);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-rest);
            display: flex;
            gap: 1.5rem;
            justify-content: space-between;
            margin: 0 0 1.35rem;
            overflow: hidden;
            padding: 1.55rem 1.7rem;
            position: relative;
        }

        .app-page-header:before {
            content: none;
        }

        .app-page-header-main,
        .app-page-header-side {
            position: relative;
            z-index: 1;
        }

        .app-page-header-main {
            flex: 1 1 auto;
            min-width: 0;
        }

        .app-page-kicker {
            color: var(--text-secondary);
            display: inline-flex;
            font-size: 0.76rem;
            font-weight: 590;
            margin-bottom: 0.44rem;
            text-transform: uppercase;
        }

        .app-page-title {
            color: var(--text);
            font-size: clamp(1.95rem, 2.6vw, 2.55rem);
            font-weight: 700;
            line-height: 1.08;
            margin: 0;
            max-width: 860px;
        }

        .app-page-description {
            color: var(--text-secondary);
            font-size: 1rem;
            font-weight: 400;
            line-height: 1.52;
            margin: 0.72rem 0 0;
            max-width: 780px;
        }

        .app-page-chip {
            align-items: center;
            background: var(--blue-soft);
            border: 1px solid rgba(0, 113, 227, 0.14);
            border-radius: 999px;
            box-shadow: none;
            color: var(--blue);
            display: inline-flex;
            flex: 0 0 auto;
            font-size: 0.78rem;
            font-weight: 590;
            margin-top: 0.12rem;
            padding: 0.46rem 0.74rem;
            white-space: nowrap;
        }

        .section-head {
            margin: 0 0 0.85rem;
        }

        .section-title {
            color: var(--text);
            font-size: 1.08rem;
            font-weight: 650;
            line-height: 1.28;
            margin: 0 0 0.28rem;
        }

        .section-description {
            color: var(--text-secondary);
            font-size: 0.9rem;
            font-weight: 400;
            line-height: 1.45;
            margin: 0;
        }

        .content-spacer {
            height: 1rem;
        }

        .content-spacer.sm {
            height: 0.65rem;
        }

        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--surface-elevated) !important;
            border: 1px solid var(--separator-soft) !important;
            border-radius: var(--radius-lg) !important;
            box-shadow: var(--shadow-rest) !important;
            transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
        }

        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: var(--separator) !important;
        }

        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlock"] {
            gap: 0.8rem;
        }

        .ui-card,
        .kpi-card,
        .insight-strip-card,
        .list-card,
        .history-card,
        .micro-kpi {
            background: var(--surface-elevated);
            border: 1px solid var(--separator-soft);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-rest);
        }

        .kpi-card {
            --kpi-color: var(--blue);
            --kpi-bg: var(--blue-soft);
            --kpi-border: rgba(0, 113, 227, 0.16);
            background:
                linear-gradient(135deg, var(--kpi-bg) 0%, rgba(255, 255, 255, 0.96) 48%, rgba(255, 255, 255, 0.94) 100%);
            border-color: var(--kpi-border);
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            margin: 0 0 1rem;
            min-height: 124px;
            padding: 1.08rem 1.12rem;
            position: relative;
            transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
        }

        .kpi-card:hover {
            border-color: var(--kpi-border);
            box-shadow: var(--shadow-hover);
            transform: translateY(-1px);
        }

        .kpi-card:before {
            background: var(--kpi-color);
            border-radius: 999px;
            content: "";
            height: 3px;
            left: 1.12rem;
            position: absolute;
            right: 1.12rem;
            top: 0.82rem;
        }

        .kpi-card.green {
            --kpi-color: var(--green);
            --kpi-bg: var(--green-soft);
            --kpi-border: rgba(36, 138, 61, 0.16);
        }
        .kpi-card.purple {
            --kpi-color: var(--purple);
            --kpi-bg: var(--purple-soft);
            --kpi-border: rgba(142, 86, 207, 0.16);
        }
        .kpi-card.orange {
            --kpi-color: var(--orange);
            --kpi-bg: var(--orange-soft);
            --kpi-border: rgba(191, 91, 0, 0.16);
        }

        .kpi-top {
            align-items: center;
            display: flex;
            gap: 0.82rem;
            justify-content: space-between;
            margin: 0.45rem 0 0.58rem;
        }

        .kpi-label {
            color: var(--text-secondary);
            font-size: 0.82rem;
            font-weight: 590;
            line-height: 1.25;
        }

        .kpi-icon {
            align-items: center;
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid var(--kpi-border);
            border-radius: var(--radius-sm);
            color: var(--kpi-color);
            display: flex;
            flex: 0 0 36px;
            font-size: 0.72rem;
            font-weight: 650;
            height: 36px;
            justify-content: center;
            width: 36px;
        }

        .kpi-value {
            color: var(--text);
            font-size: 1.68rem;
            font-weight: 700;
            line-height: 1.06;
            overflow-wrap: anywhere;
        }

        .kpi-help {
            color: var(--text-secondary);
            font-size: 0.79rem;
            line-height: 1.42;
            margin-top: 0.42rem;
        }

        .role-hero,
        .action-banner {
            background: var(--surface-elevated);
            border: 1px solid var(--separator-soft);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-rest);
            color: var(--text);
            margin: 0 0 1rem;
            overflow: hidden;
            position: relative;
        }

        .role-hero {
            padding: 1.45rem;
        }

        .role-hero-top,
        .action-banner-main {
            align-items: flex-start;
            display: flex;
            gap: 1rem;
            justify-content: space-between;
            position: relative;
            z-index: 1;
        }

        .role-hero-kicker {
            color: var(--text-secondary);
            font-size: 0.72rem;
            font-weight: 590;
            margin-bottom: 0.36rem;
            text-transform: uppercase;
        }

        .role-hero-title {
            color: var(--text);
            font-size: 1.55rem;
            font-weight: 700;
            line-height: 1.14;
            margin: 0;
        }

        .role-hero-subtitle {
            color: var(--text-secondary);
            font-size: 0.92rem;
            line-height: 1.55;
            margin-top: 0.6rem;
            max-width: 720px;
        }

        .role-hero-icon,
        .action-banner-icon {
            align-items: center;
            background: var(--blue-soft);
            border: 1px solid rgba(0, 113, 227, 0.14);
            border-radius: var(--radius-md);
            box-shadow: none;
            color: var(--blue);
            display: flex;
            font-weight: 650;
            justify-content: center;
        }

        .role-hero-icon {
            flex: 0 0 56px;
            font-size: 0.88rem;
            height: 56px;
            width: 56px;
        }

        .role-hero-stats,
        .insight-strip,
        .history-grid,
        .micro-kpis {
            display: grid;
            gap: 0.9rem;
            margin-top: 1rem;
        }

        .role-hero-stats,
        .insight-strip,
        .micro-kpis {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }

        .history-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .role-hero-stat {
            background: var(--surface-muted);
            border: 1px solid var(--separator-soft);
            border-radius: var(--radius-md);
            padding: 0.86rem 0.92rem;
        }

        .role-hero-stat:nth-child(2) {
            background: var(--surface-muted);
        }

        .role-hero-stat:nth-child(3) {
            background: var(--surface-muted);
        }

        .role-hero-stat-value {
            color: var(--text);
            font-size: 1.16rem;
            font-weight: 700;
            line-height: 1;
        }

        .role-hero-stat-label {
            color: var(--text-secondary);
            font-size: 0.74rem;
            font-weight: 590;
            margin-top: 0.38rem;
        }

        .insight-strip {
            margin: 0 0 1rem;
        }

        .insight-strip-card,
        .history-card,
        .micro-kpi,
        .list-card {
            padding: 1rem 1.08rem;
        }

        .insight-strip-label,
        .micro-kpi-label {
            color: var(--text-tertiary);
            font-size: 0.69rem;
            font-weight: 590;
            text-transform: uppercase;
        }

        .insight-strip-value,
        .micro-kpi-value {
            color: var(--text);
            font-size: 1.02rem;
            font-weight: 650;
            margin-top: 0.36rem;
        }

        .insight-strip-copy {
            color: var(--text-secondary);
            font-size: 0.81rem;
            line-height: 1.5;
            margin-top: 0.36rem;
        }

        .action-banner {
            align-items: center;
            display: flex;
            gap: 0.95rem;
            justify-content: space-between;
            padding: 1.08rem 1.15rem;
        }

        .action-banner-main {
            align-items: center;
            justify-content: flex-start;
        }

        .action-banner-title {
            color: var(--text);
            font-size: 1rem;
            font-weight: 650;
            line-height: 1.2;
        }

        .action-banner-copy {
            color: var(--text-secondary);
            font-size: 0.82rem;
            line-height: 1.5;
            margin-top: 0.22rem;
        }

        .action-banner-icon {
            flex: 0 0 44px;
            height: 44px;
            width: 44px;
        }

        .warning-card {
            align-items: flex-start;
            background: var(--orange-soft);
            border: 1px solid rgba(191, 91, 0, 0.16);
            border-radius: var(--radius-md);
            color: #713f00;
            display: flex;
            gap: 0.85rem;
            margin: 0.85rem 0;
            padding: 1rem 1.05rem;
        }

        .warning-card-icon {
            align-items: center;
            background: rgba(191, 91, 0, 0.12);
            border-radius: var(--radius-sm);
            color: var(--orange);
            display: flex;
            flex: 0 0 36px;
            font-size: 0.78rem;
            font-weight: 700;
            height: 36px;
            justify-content: center;
            width: 36px;
        }

        .warning-card-title {
            color: #713f00;
            font-size: 0.94rem;
            font-weight: 650;
            margin-bottom: 0.16rem;
        }

        .warning-card-copy {
            color: #7a4400;
            font-size: 0.84rem;
            line-height: 1.5;
        }

        .list-card {
            align-items: center;
            display: flex;
            gap: 0.9rem;
            margin: 0.78rem 0;
            transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
        }

        .list-card:hover {
            border-color: var(--separator);
            box-shadow: var(--shadow-hover);
            transform: translateY(-1px);
        }

        .list-card-thumb {
            align-items: center;
            background: var(--blue-soft);
            border: 1px solid rgba(0, 113, 227, 0.14);
            border-radius: var(--radius-md);
            color: var(--blue);
            display: flex;
            flex: 0 0 48px;
            font-size: 0.76rem;
            font-weight: 700;
            height: 48px;
            justify-content: center;
            width: 48px;
        }

        .list-card-content {
            flex: 1;
            min-width: 0;
        }

        .list-card-head {
            align-items: center;
            display: flex;
            flex-wrap: wrap;
            gap: 0.52rem;
        }

        .list-card-title,
        .history-card-title {
            color: var(--text);
            font-size: 0.92rem;
            font-weight: 650;
            line-height: 1.24;
        }

        .list-card-meta,
        .history-card-meta {
            color: var(--text-secondary);
            font-size: 0.79rem;
            line-height: 1.5;
            margin-top: 0.24rem;
        }

        .status-pill,
        .list-card-badge,
        .history-card-badge {
            border: 1px solid transparent;
            border-radius: 999px;
            display: inline-flex;
            font-size: 0.7rem;
            font-weight: 590;
            padding: 0.3rem 0.62rem;
            white-space: nowrap;
        }

        .status-pill.success,
        .list-card-badge.success {
            background: var(--green-soft);
            border-color: rgba(36, 138, 61, 0.16);
            color: var(--green);
        }

        .status-pill.warning,
        .list-card-badge.warning {
            background: var(--orange-soft);
            border-color: rgba(191, 91, 0, 0.16);
            color: var(--orange);
        }

        .status-pill.danger,
        .list-card-badge.danger {
            background: var(--red-soft);
            border-color: rgba(215, 0, 21, 0.16);
            color: var(--red);
        }

        .status-pill.neutral,
        .list-card-badge.neutral,
        .history-card-badge {
            background: var(--blue-soft);
            border-color: rgba(0, 113, 227, 0.14);
            color: var(--blue);
        }

        div[data-testid="stFileUploader"] section {
            background: var(--surface-muted);
            border: 1.5px dashed rgba(0, 113, 227, 0.24);
            border-radius: var(--radius-lg) !important;
            min-height: 136px;
            padding: 1.08rem 1.1rem;
            transition: border-color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
        }

        div[data-testid="stFileUploader"] section:hover {
            background: var(--blue-soft);
            border-color: rgba(0, 113, 227, 0.46);
            box-shadow: inset 0 0 0 1px rgba(0, 113, 227, 0.04);
        }

        div[data-testid="stFileUploader"] button {
            border-radius: 999px !important;
            min-width: 132px;
            white-space: nowrap;
        }

        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button,
        div[data-testid="stDownloadButton"] > button,
        button[kind="secondary"] {
            background: var(--surface) !important;
            border: 1px solid var(--separator) !important;
            border-radius: 999px !important;
            box-shadow: none !important;
            color: var(--text) !important;
            min-height: 42px;
            padding: 0.48rem 0.95rem;
            transition: background 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease, color 0.16s ease, transform 0.16s ease;
        }

        div[data-testid="stButton"] > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover,
        button[kind="secondary"]:hover {
            background: var(--page-bg-soft) !important;
            border-color: var(--separator-strong) !important;
            color: var(--text) !important;
            transform: translateY(-1px);
        }

        div[data-testid="stButton"] > button:focus,
        div[data-testid="stFormSubmitButton"] > button:focus,
        div[data-testid="stDownloadButton"] > button:focus {
            box-shadow: var(--focus-ring) !important;
            outline: none !important;
        }

        div[data-testid="stButton"] > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button[kind="primary"],
        div[data-testid="stDownloadButton"] > button[kind="primary"] {
            background: var(--blue) !important;
            border: 1px solid var(--blue) !important;
            box-shadow: none !important;
            color: var(--text-inverse) !important;
        }

        div[data-testid="stButton"] > button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover,
        div[data-testid="stDownloadButton"] > button[kind="primary"]:hover {
            background: var(--blue-hover) !important;
            border-color: var(--blue-hover) !important;
            color: var(--text-inverse) !important;
        }

        div[data-testid="stButton"] > button[kind="primary"]:active,
        div[data-testid="stFormSubmitButton"] > button[kind="primary"]:active,
        div[data-testid="stDownloadButton"] > button[kind="primary"]:active {
            background: var(--blue-pressed) !important;
            border-color: var(--blue-pressed) !important;
        }

        div[data-testid="stButton"] > button p,
        div[data-testid="stFormSubmitButton"] > button p,
        div[data-testid="stDownloadButton"] > button p {
            font-size: 0.9rem !important;
            font-weight: 590 !important;
            line-height: 1.15 !important;
            white-space: normal !important;
        }

        div[data-baseweb="select"] > div,
        div[data-testid="stTextInputRootElement"] > div,
        div[data-testid="stTextAreaRootElement"] > div,
        div[data-testid="stNumberInput"] input {
            background: rgba(255, 255, 255, 0.94) !important;
            border: 1px solid rgba(24, 45, 80, 0.14) !important;
            border-radius: var(--radius-sm) !important;
            box-shadow: none !important;
            min-height: 42px;
            transition: border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
        }

        div[data-baseweb="select"] > div:hover,
        div[data-testid="stTextInputRootElement"] > div:hover,
        div[data-testid="stTextAreaRootElement"] > div:hover,
        div[data-testid="stNumberInput"] input:hover {
            border-color: var(--separator-strong) !important;
        }

        div[data-baseweb="select"] > div:focus-within,
        div[data-testid="stTextInputRootElement"] > div:focus-within,
        div[data-testid="stTextAreaRootElement"] > div:focus-within,
        div[data-testid="stNumberInput"] input:focus {
            border-color: rgba(0, 113, 227, 0.55) !important;
            box-shadow: var(--focus-ring) !important;
        }

        div[data-baseweb="select"] span,
        div[data-testid="stTextInputRootElement"] input,
        div[data-testid="stTextAreaRootElement"] textarea,
        div[data-testid="stNumberInput"] input {
            color: var(--text) !important;
            font-size: 0.92rem !important;
            font-weight: 400 !important;
        }

        div[data-testid="stRadio"] label,
        div[data-testid="stCheckbox"] label {
            color: var(--text) !important;
            font-weight: 500 !important;
        }

        div[data-testid="stMetric"] {
            background: var(--surface-elevated) !important;
            border: 1px solid var(--separator-soft) !important;
            border-radius: var(--radius-lg) !important;
            box-shadow: var(--shadow-rest) !important;
            min-height: 98px;
            padding: 0.95rem 1rem !important;
        }

        div[data-testid="stMetricLabel"] p {
            color: var(--text-secondary) !important;
            font-size: 0.79rem !important;
            font-weight: 590 !important;
        }

        div[data-testid="stMetricValue"] {
            color: var(--text) !important;
            font-size: 1.48rem !important;
            font-weight: 700 !important;
            line-height: 1.08 !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid var(--separator-soft);
            border-radius: 999px;
            display: inline-flex;
            gap: 0.2rem;
            padding: 0.25rem;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            color: var(--text-secondary);
            font-size: 0.87rem;
            font-weight: 590 !important;
            min-height: 36px;
            padding: 0.36rem 0.9rem;
            transition: background 0.16s ease, color 0.16s ease;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background: var(--sky-soft);
            color: var(--text);
        }

        .stTabs [aria-selected="true"] {
            background: var(--surface);
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
            color: var(--text) !important;
        }

        .stDataFrame,
        div[data-testid="stDataFrame"] {
            background: var(--surface-elevated);
            border: 1px solid var(--separator-soft);
            border-radius: var(--radius-lg) !important;
            box-shadow: var(--shadow-rest);
            overflow: hidden;
        }

        div[data-testid="stDataFrame"] [role="columnheader"] {
            background: var(--page-bg-soft) !important;
            color: var(--text) !important;
            font-weight: 650 !important;
        }

        div[data-testid="stDataFrame"] [role="row"]:hover {
            background: var(--sky-soft) !important;
        }

        [data-testid="stAlert"] {
            border-radius: var(--radius-md) !important;
            border: 1px solid var(--separator-soft) !important;
        }

        .history-card-top {
            align-items: center;
            display: flex;
            gap: 0.65rem;
            justify-content: space-between;
        }

        .footer {
            border-top: 1px solid var(--separator-soft);
            color: var(--text-tertiary);
            font-size: 0.76rem;
            margin-top: 1.9rem;
            padding: 1rem 0 0.2rem;
            text-align: center;
        }

        [data-testid="stSidebar"] {
            background: rgba(251, 251, 253, 0.92) !important;
            border-right: 1px solid var(--separator-soft);
        }

        [data-testid="collapsedControl"] {
            color: var(--text);
        }

        img {
            border-radius: var(--radius-md);
        }

        ::-webkit-scrollbar {
            height: 8px;
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: transparent;
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(0, 0, 0, 0.20);
            border-radius: 999px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(0, 0, 0, 0.30);
        }

        @media (max-width: 900px) {
            .main .block-container,
            [data-testid="stMain"] .block-container {
                padding: 1rem;
            }

            .app-page-header {
                flex-direction: column;
            }

            .app-page-chip {
                margin-top: 0;
            }

            .role-hero-top,
            .action-banner-main {
                align-items: flex-start;
            }

            .role-hero-stats,
            .insight-strip,
            .history-grid,
            .micro-kpis {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 640px) {
            html,
            body,
            .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stMain"] {
                max-width: 100%;
                overflow-x: hidden;
            }

            .main .block-container,
            [data-testid="stMain"] .block-container {
                padding: 0.78rem 0.72rem 1.4rem;
            }

            [data-testid="stMain"] [data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
                gap: 0.85rem !important;
            }

            [data-testid="stMain"] [data-testid="stHorizontalBlock"] > div[data-testid="column"] {
                flex: 1 1 100% !important;
                min-width: 0 !important;
                width: 100% !important;
            }

            [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"],
            .app-page-header,
            .role-hero,
            .action-banner,
            .ui-card,
            .kpi-card,
            .insight-strip-card,
            .list-card,
            .history-card,
            .micro-kpi,
            .home-header,
            .monitor-hero,
            .compliance-card {
                border-radius: 14px !important;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
            }

            .app-page-header,
            .role-hero,
            .action-banner,
            .home-header,
            .monitor-hero,
            .compliance-card {
                padding: 1rem !important;
            }

            .app-page-title,
            .home-title {
                font-size: 1.55rem !important;
                line-height: 1.14 !important;
                overflow-wrap: anywhere;
            }

            .role-hero-title,
            .monitor-title {
                font-size: 1.28rem !important;
                line-height: 1.18 !important;
                overflow-wrap: anywhere;
            }

            .app-page-description,
            .home-subtitle,
            .role-hero-subtitle,
            .monitor-copy,
            .section-description {
                font-size: 0.88rem !important;
                line-height: 1.48 !important;
            }

            .app-page-header,
            .role-hero-top,
            .action-banner-main,
            .home-header,
            .monitor-hero-top,
            .home-panel-head,
            .history-card-top,
            .compliance-result-top {
                align-items: flex-start !important;
                flex-direction: column !important;
            }

            .app-page-chip,
            .home-chip,
            .status-pill,
            .list-card-badge,
            .history-card-badge {
                max-width: 100%;
                white-space: normal;
            }

            .kpi-card {
                margin-bottom: 0;
                min-height: auto;
                padding: 0.95rem 1rem;
            }

            .kpi-value,
            div[data-testid="stMetricValue"] {
                font-size: 1.28rem !important;
                overflow-wrap: anywhere;
            }

            .role-hero-stats,
            .insight-strip,
            .history-grid,
            .micro-kpis,
            .monitor-stats,
            .compliance-metrics,
            .compliance-compare-grid,
            .compliance-confidence {
                grid-template-columns: 1fr !important;
            }

            .role-hero-icon,
            .action-banner-icon,
            .monitor-icon {
                flex-basis: 40px !important;
                height: 40px !important;
                width: 40px !important;
            }

            .list-card,
            .warning-card {
                align-items: flex-start;
                padding: 0.9rem;
            }

            div[data-testid="stMetric"] {
                min-height: auto;
                padding: 0.85rem 0.9rem !important;
            }

            div[data-testid="stButton"] > button,
            div[data-testid="stFormSubmitButton"] > button,
            div[data-testid="stDownloadButton"] > button,
            div[data-testid="stFileUploader"] button {
                min-width: 0 !important;
                width: 100% !important;
            }

            div[data-testid="stFileUploader"] section {
                min-height: auto;
                padding: 0.85rem !important;
            }

            .stTabs [data-baseweb="tab-list"] {
                border-radius: 14px;
                display: flex;
                max-width: 100%;
                overflow-x: auto;
                width: 100%;
            }

            .stTabs [data-baseweb="tab"] {
                flex: 0 0 auto;
            }

            .stDataFrame,
            div[data-testid="stDataFrame"],
            .plano-grid-wrap {
                max-width: 100%;
                overflow-x: auto !important;
            }

            .plano-grid {
                min-width: 520px !important;
            }

            img,
            [data-testid="stImage"] img {
                height: auto;
                max-width: 100%;
            }

            .footer {
                font-size: 0.72rem;
                line-height: 1.4;
            }
        }
        </style>
        """
    )
