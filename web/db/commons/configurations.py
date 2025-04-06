import random

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
        ("SBUX", "Starbucks Corporation"),
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


def get_companies(n=None, sectors_filter=None, shuffle=False):
    """
    Retorna listas de abreviaturas y nombres de empresas, equilibrando por sectores.

    Args:
        n (int): Número total de empresas deseado.
        sectors_filter (list[str]): Lista opcional de sectores a incluir.
        shuffle (bool): Si True, baraja el orden de empresas antes de seleccionar.

    Returns:
        Tuple[List[str], List[str]]
    """
    # Filtra sectores si se especifica
    filtered_sectors = {
        k: v for k, v in sectors.items() if not sectors_filter or k in sectors_filter
    }

    all_companies = []
    max_len = max(len(c) for c in filtered_sectors.values())

    # Intercalar por sector
    for i in range(max_len):
        for sector in filtered_sectors.values():
            if i < len(sector):
                all_companies.append(sector[i])

    if shuffle:
        random.shuffle(all_companies)

    # Ajustar cantidad
    if n is not None:
        total = sum(len(c) for c in filtered_sectors.values())
        if not (1 <= n <= total):
            raise ValueError(f"Portfolio length must be between 1 and {total}")
        all_companies = all_companies[:n]

    abvs = [c[0] for c in all_companies]
    names = [c[1] for c in all_companies]
    return abvs, names
