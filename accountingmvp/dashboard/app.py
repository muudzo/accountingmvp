"""
Payment Reconciliation Dashboard
================================
Main Streamlit application for the payment reconciliation system.

Run with: streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


import pandas as pd
import streamlit as st

from src.models.enums import MatchStatus, TransactionSource
from src.normalizer import DataValidator, NormalizationPipeline
from src.parsers import BankCSVParser, ParserFactory
from src.reconciliation import ReconciliationEngine, ReportGenerator

# Page config
st.set_page_config(
    page_title="Payment Reconciliation",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .match-high { color: #28a745; font-weight: bold; }
    .match-medium { color: #ffc107; font-weight: bold; }
    .match-low { color: #dc3545; font-weight: bold; }
</style>
""",
    unsafe_allow_html=True,
)


def init_session_state():
    """Initialize session state variables."""
    if "source_data" not in st.session_state:
        st.session_state.source_data = None
    if "target_data" not in st.session_state:
        st.session_state.target_data = None
    if "matches" not in st.session_state:
        st.session_state.matches = None
    if "summary" not in st.session_state:
        st.session_state.summary = None


def parse_uploaded_file(uploaded_file, source_type: TransactionSource):
    """Parse an uploaded file and return normalized transactions."""
    # Read content
    content = uploaded_file.read().decode("utf-8")

    # Save temporarily
    temp_path = f"/tmp/{uploaded_file.name}"
    with open(temp_path, "w") as f:
        f.write(content)

    # Get parser
    parser = ParserFactory.get_parser(temp_path)
    if not parser:
        # Fallback to bank CSV parser
        parser = BankCSVParser()

    # Parse
    raw_transactions = parser.parse(temp_path)

    # Normalize
    pipeline = NormalizationPipeline(source_type)
    normalized = pipeline.process(raw_transactions)

    # Validate
    validator = DataValidator()
    valid, invalid = validator.validate_batch(normalized)

    return valid, invalid, validator.get_report()


def render_sidebar():
    """Render the sidebar with file upload."""
    st.sidebar.header("📁 Upload Files")

    st.sidebar.subheader("Source (Bank Statement)")
    source_file = st.sidebar.file_uploader(
        "Upload bank CSV",
        type=["csv", "txt"],
        key="source_upload",
        help="Upload your bank statement in CSV format",
    )

    st.sidebar.subheader("Target (Payment Records)")
    target_file = st.sidebar.file_uploader(
        "Upload payment records",
        type=["csv", "txt"],
        key="target_upload",
        help="Upload Ecocash, ZIPIT, or invoice records",
    )

    st.sidebar.divider()

    st.sidebar.subheader("⚙️ Settings")
    confidence_threshold = (
        st.sidebar.slider(
            "Auto-match confidence",
            min_value=50,
            max_value=100,
            value=85,
            help="Minimum confidence % for automatic matching",
        )
        / 100
    )

    return source_file, target_file, confidence_threshold


def render_data_preview(df: pd.DataFrame, title: str):
    """Render a data preview section."""
    with st.expander(f"📊 {title} ({len(df)} rows)", expanded=False):
        st.dataframe(df, use_container_width=True)


def render_summary_metrics(summary):
    """Render summary metrics cards."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "✅ Matched", summary.matched_count, delta=f"{summary.match_rate:.0%} rate"
        )

    with col2:
        st.metric("❓ Unmatched Source", summary.unmatched_source_count)

    with col3:
        st.metric("🔍 Manual Review", summary.manual_review_count)

    with col4:
        st.metric("💰 Matched Amount", f"${summary.total_matched_amount:,.2f}")


def render_match_results(matches, summary):
    """Render match results."""
    st.header("📋 Reconciliation Results")

    # Summary metrics
    render_summary_metrics(summary)

    st.divider()

    # Tabs for different match statuses
    tab1, tab2, tab3 = st.tabs(["✅ Matched", "🔍 Manual Review", "❌ Unmatched"])

    matched = [m for m in matches if m.status == MatchStatus.MATCHED]
    review = [m for m in matches if m.status == MatchStatus.MANUAL_REVIEW]
    unmatched = [m for m in matches if m.status == MatchStatus.UNMATCHED]

    with tab1:
        if matched:
            for m in matched[:50]:  # Limit display
                with st.container():
                    col1, col2, col3 = st.columns([4, 4, 2])
                    with col1:
                        st.markdown(
                            f"**Source:** {m.source_transaction.description[:40]}..."
                        )
                        st.caption(
                            f"${m.source_transaction.amount} | {m.source_transaction.transaction_date}"
                        )
                    with col2:
                        st.markdown(
                            f"**Target:** {m.target_transaction.description[:40]}..."
                        )
                        st.caption(
                            f"${m.target_transaction.amount} | {m.target_transaction.transaction_date}"
                        )
                    with col3:
                        st.markdown(
                            f"<span class='match-high'>{m.score.total_score:.0%}</span>",
                            unsafe_allow_html=True,
                        )
                    st.divider()
        else:
            st.info("No automatic matches found.")

    with tab2:
        if review:
            for m in review[:50]:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
                    with col1:
                        st.markdown(
                            f"**Source:** {m.source_transaction.description[:30]}..."
                        )
                        st.caption(f"${m.source_transaction.amount}")
                    with col2:
                        st.markdown(
                            f"**Target:** {m.target_transaction.description[:30]}..."
                        )
                        st.caption(f"${m.target_transaction.amount}")
                    with col3:
                        st.markdown(
                            f"<span class='match-medium'>{m.score.total_score:.0%}</span>",
                            unsafe_allow_html=True,
                        )
                    with col4:
                        if st.button(
                            "✅ Approve", key=f"approve_{m.source_transaction.id}"
                        ):
                            st.success("Approved!")
                        if st.button(
                            "❌ Reject", key=f"reject_{m.source_transaction.id}"
                        ):
                            st.warning("Rejected")
                    st.divider()
        else:
            st.success("No items require manual review!")

    with tab3:
        if unmatched:
            st.warning(f"{len(unmatched)} transactions could not be matched.")
            for m in unmatched[:20]:
                st.text(
                    f"• {m.source_transaction.description[:50]} - ${m.source_transaction.amount}"
                )
        else:
            st.success("All transactions matched!")


def render_download_section(matches, summary):
    """Render report download section."""
    st.header("📥 Download Report")

    col1, col2 = st.columns(2)

    with col1:
        reporter = ReportGenerator()
        csv_data = reporter.generate_csv(matches)

        st.download_button(
            label="📄 Download CSV Report",
            data=csv_data,
            file_name="reconciliation_report.csv",
            mime="text/csv",
        )

    with col2:
        # Excel download requires file path, so we provide CSV alternative
        st.download_button(
            label="📊 Download Details (CSV)",
            data=csv_data,
            file_name="reconciliation_details.csv",
            mime="text/csv",
        )


def main():
    """Main application."""
    init_session_state()

    st.title("💸 Payment Reconciliation Layer")
    st.caption("Reconcile bank statements against payment records with fuzzy matching")

    # Sidebar
    source_file, target_file, confidence_threshold = render_sidebar()

    # Main content
    if source_file and target_file:
        # Process button
        if st.button("🚀 Run Reconciliation", type="primary", use_container_width=True):
            with st.spinner("Processing files..."):
                try:
                    # Parse source
                    source_txns, source_invalid, source_report = parse_uploaded_file(
                        source_file, TransactionSource.BANK_STATEMENT
                    )
                    st.session_state.source_data = source_txns

                    # Parse target
                    target_txns, target_invalid, target_report = parse_uploaded_file(
                        target_file, TransactionSource.ECOCASH
                    )
                    st.session_state.target_data = target_txns

                    # Show parsing results
                    st.success(
                        f"✅ Parsed {len(source_txns)} source and {len(target_txns)} target transactions"
                    )

                    if source_invalid or target_invalid:
                        st.warning(
                            f"⚠️ {len(source_invalid)} source and {len(target_invalid)} target rows skipped due to validation errors"
                        )

                    # Run reconciliation
                    engine = ReconciliationEngine(
                        confidence_threshold=confidence_threshold
                    )
                    matches, summary = engine.reconcile(source_txns, target_txns)

                    st.session_state.matches = matches
                    st.session_state.summary = summary

                except Exception as e:
                    st.error(f"Error processing files: {str(e)}")
                    st.exception(e)

        # Show results if available
        if st.session_state.matches:
            render_match_results(st.session_state.matches, st.session_state.summary)
            st.divider()
            render_download_section(st.session_state.matches, st.session_state.summary)

    else:
        # Welcome message
        st.info(
            "👈 Upload both source (bank statement) and target (payment records) files to begin reconciliation."
        )

        # Demo data section
        with st.expander("📚 Sample Data Format"):
            st.markdown(
                """
            **Bank Statement CSV (Source):**
            ```
            Date,Reference,Amount,Description
            2024-01-15,TXN001,1500.00,Payment from ABC Corp
            2024-01-16,TXN002,-250.00,Transfer to XYZ Ltd
            ```

            **Ecocash/Payment Record (Target):**
            ```
            Date,Reference,Amount,Description
            15/01/2024,EC001,1500,ABC Corporation payment
            16/01/2024,EC002,250,XYZ Limited
            ```
            """
            )


if __name__ == "__main__":
    main()
