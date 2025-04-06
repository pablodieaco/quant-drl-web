from commons.db_connection import connect_db

from web.commons.logging import logger

# Dictionary of companies by sector
sectors = {
    "Healthcare": [
        ("LLY", "Lilly"),
        ("UNH", "UnitedHealth"),
        ("JNJ", "Johnson & Johnson"),
        ("PFE", "Pfizer"),
        ("NVS", "Novartis (Switzerland)"),
        ("ROG.SW", "Roche (Switzerland)"),
        ("SAN.PA", "Sanofi (France)"),
        ("BAYN.DE", "Bayer (Germany)"),
    ],
    "Technology": [
        ("AAPL", "Apple"),
        ("MSFT", "Microsoft"),
        ("IBM", "IBM"),
        ("GOOGL", "Alphabet"),
        ("SAP.DE", "SAP (Germany)"),
        ("ASML.AS", "ASML (Netherlands)"),
        ("INFY", "Infosys (India)"),
        ("NXPI", "NXP Semiconductors (Netherlands)"),
    ],
    "Consumer Cyclical": [
        ("AMZN", "Amazon"),
        ("HD", "Home Depot"),
        ("WMT", "Walmart"),
        ("MCD", "McDonald's"),
        ("LVMH.PA", "LVMH (France)"),
        ("PUM.DE", "Puma (Germany)"),
        ("ADS.DE", "Adidas (Germany)"),
        ("RMS.PA", "Hermès (France)"),
    ],
    "Financial Services": [
        ("JPM", "JPMorgan Chase"),
        ("BAC", "Bank of America"),
        ("V", "Visa"),
        ("MA", "Mastercard"),
        ("HSBA.L", "HSBC (UK)"),
        ("BNP.PA", "BNP Paribas (France)"),
        ("DBK.DE", "Deutsche Bank (Germany)"),
        ("INGA.AS", "ING Group (Netherlands)"),
    ],
    "Consumer Defensive": [
        ("WMT", "Walmart"),
        ("KO", "Coca-Cola"),
        ("PEP", "PepsiCo"),
        ("PG", "Procter & Gamble"),
        ("NESN.SW", "Nestlé (Switzerland)"),
        ("ULVR.L", "Unilever (UK)"),
        ("DANOY", "Danone (France)"),
        ("BATS.L", "British American Tobacco (UK)"),
    ],
    "Energy": [
        ("CVX", "Chevron"),
        ("COP", "ConocoPhillips"),
        ("EOG", "EOG Resources"),
        ("XOM", "ExxonMobil"),
        ("BP.L", "BP (UK)"),
        ("TTE.PA", "TotalEnergies (France)"),
        ("SHEL.L", "Shell (UK)"),
        ("ENI.MI", "Eni (Italy)"),
    ],
    "Industrials": [
        ("CAT", "Caterpillar"),
        ("BA", "Boeing"),
        ("GE", "General Electric"),
        ("HON", "Honeywell"),
        ("AIR.PA", "Airbus (France)"),
        ("SIE.DE", "Siemens (Germany)"),
        ("RWE.DE", "RWE (Germany)"),
        ("FLTR.L", "Flutter Entertainment (UK)"),
    ],
    "Utilities": [
        ("NEE", "NextEra Energy"),
        ("DUK", "Duke Energy"),
        ("SO", "Southern Company"),
        ("D", "Dominion Energy"),
        ("ENEL.MI", "Enel (Italy)"),
        ("IBE.MC", "Iberdrola (Spain)"),
        ("NG.L", "National Grid (UK)"),
        ("VIE.PA", "Veolia (France)"),
    ],
    "Materials": [
        ("LIN", "Linde"),
        ("SHW", "Sherwin-Williams"),
        ("APD", "Air Products"),
        ("NEM", "Newmont Corporation"),
        ("BAS.DE", "BASF (Germany)"),
        ("GLEN.L", "Glencore (UK)"),
        ("ARKR.DE", "ArcelorMittal (Luxembourg)"),
        ("LON:CRH", "CRH (Ireland)"),
    ],
    "Telecommunications": [
        ("VZ", "Verizon"),
        ("T", "AT&T"),
        ("TMUS", "T-Mobile"),
        ("CMCSA", "Comcast"),
        ("DTE.DE", "Deutsche Telekom (Germany)"),
        ("ORAN.PA", "Orange (France)"),
        ("BT.L", "BT Group (UK)"),
        ("VOD.L", "Vodafone (UK)"),
    ],
}


def upload_companies(add_cash=True):
    """Upload all companies to the database, avoiding duplicates."""
    conn = None
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            for sector, companies in sectors.items():
                for ticker, name in companies:
                    cursor.execute(
                        "SELECT 1 FROM companies WHERE ticker = %s", (ticker,)
                    )
                    if not cursor.fetchone():
                        cursor.execute(
                            """
                            INSERT INTO companies (name, ticker, sector)
                            VALUES (%s, %s, %s)
                            """,
                            (name, ticker, sector),
                        )
                        logger.info(f"Added {name} ({ticker}) in {sector}")
                    else:
                        logger.debug(f"Skipped duplicate: {ticker}")

            if add_cash:
                cursor.execute("SELECT 1 FROM companies WHERE ticker = 'CASH'")
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO companies (name, ticker) VALUES (%s, %s)",
                        ("Cash", "CASH"),
                    )
                    logger.info("Added synthetic 'Cash' asset")

        conn.commit()
        logger.success("Companies upload completed!")

    except Exception as e:
        logger.exception(f"Error during upload: {e}")

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    upload_companies()
