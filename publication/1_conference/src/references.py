"""Bibliography for the ISGT Asia AQF paper.

Single source of truth for every citation: APA in-text form, APA reference-list
form, CSL-JSON (so the Word citations can be real Zotero fields) and RIS export.
All entries were verified against Crossref/OpenAlex/publisher pages, 2026-08-28.
"""

from __future__ import annotations

from pathlib import Path

# key -> record.  "intext" is the APA in-text form WITHOUT the outer brackets.
REFS: dict[str, dict] = {
    "palensky2011": {
        "intext": "Palensky & Dietrich, 2011",
        "apa": "Palensky, P., & Dietrich, D. (2011). Demand side management: Demand "
               "response, intelligent energy systems, and smart loads. IEEE Transactions "
               "on Industrial Informatics, 7(3), 381–388. https://doi.org/10.1109/TII.2011.2158841",
        "csl": {
            "type": "article-journal", "title": "Demand Side Management: Demand Response, "
            "Intelligent Energy Systems, and Smart Loads",
            "container-title": "IEEE Transactions on Industrial Informatics",
            "volume": "7", "issue": "3", "page": "381-388", "DOI": "10.1109/TII.2011.2158841",
            "issued": {"date-parts": [[2011]]},
            "author": [{"family": "Palensky", "given": "Peter"},
                       {"family": "Dietrich", "given": "Dietmar"}],
        },
        "ris_type": "JOUR",
    },
    "wang2019": {
        "intext": "Wang et al., 2019",
        "apa": "Wang, Y., Chen, Q., Hong, T., & Kang, C. (2019). Review of smart meter data "
               "analytics: Applications, methodologies, and challenges. IEEE Transactions on "
               "Smart Grid, 10(3), 3125–3148. https://doi.org/10.1109/TSG.2018.2818167",
        "csl": {
            "type": "article-journal", "title": "Review of Smart Meter Data Analytics: "
            "Applications, Methodologies, and Challenges",
            "container-title": "IEEE Transactions on Smart Grid",
            "volume": "10", "issue": "3", "page": "3125-3148", "DOI": "10.1109/TSG.2018.2818167",
            "issued": {"date-parts": [[2019]]},
            "author": [{"family": "Wang", "given": "Yi"}, {"family": "Chen", "given": "Qixin"},
                       {"family": "Hong", "given": "Tao"}, {"family": "Kang", "given": "Chongqing"}],
        },
        "ris_type": "JOUR",
    },
    "kwac2014": {
        "intext": "Kwac et al., 2014",
        "apa": "Kwac, J., Flora, J., & Rajagopal, R. (2014). Household energy consumption "
               "segmentation using hourly data. IEEE Transactions on Smart Grid, 5(1), "
               "420–430. https://doi.org/10.1109/TSG.2013.2278477",
        "csl": {
            "type": "article-journal", "title": "Household Energy Consumption Segmentation "
            "Using Hourly Data", "container-title": "IEEE Transactions on Smart Grid",
            "volume": "5", "issue": "1", "page": "420-430", "DOI": "10.1109/TSG.2013.2278477",
            "issued": {"date-parts": [[2014]]},
            "author": [{"family": "Kwac", "given": "Jungsuk"}, {"family": "Flora", "given": "June"},
                       {"family": "Rajagopal", "given": "Ram"}],
        },
        "ris_type": "JOUR",
    },
    "hart1992": {
        "intext": "Hart, 1992",
        "apa": "Hart, G. W. (1992). Nonintrusive appliance load monitoring. Proceedings of the "
               "IEEE, 80(12), 1870–1891. https://doi.org/10.1109/5.192069",
        "csl": {
            "type": "article-journal", "title": "Nonintrusive appliance load monitoring",
            "container-title": "Proceedings of the IEEE", "volume": "80", "issue": "12",
            "page": "1870-1891", "DOI": "10.1109/5.192069", "issued": {"date-parts": [[1992]]},
            "author": [{"family": "Hart", "given": "G. W."}],
        },
        "ris_type": "JOUR",
    },
    "valentini2022": {
        "intext": "Valentini et al., 2022",
        "apa": "Valentini, O., Andreadou, N., Bertoldi, P., Lucas, A., Saviuc, I., & Kotsakis, E. "
               "(2022). Demand response impact evaluation: A review of methods for estimating the "
               "customer baseline load. Energies, 15(14), 5259. https://doi.org/10.3390/en15145259",
        "csl": {
            "type": "article-journal", "title": "Demand Response Impact Evaluation: A Review of "
            "Methods for Estimating the Customer Baseline Load", "container-title": "Energies",
            "volume": "15", "issue": "14", "page": "5259", "DOI": "10.3390/en15145259",
            "issued": {"date-parts": [[2022]]},
            "author": [{"family": "Valentini", "given": "Ottavia"},
                       {"family": "Andreadou", "given": "Nikoleta"},
                       {"family": "Bertoldi", "given": "Paolo"},
                       {"family": "Lucas", "given": "Alexandre"},
                       {"family": "Saviuc", "given": "Iolanda"},
                       {"family": "Kotsakis", "given": "Evangelos"}],
        },
        "ris_type": "JOUR",
    },
    "mathieu2011": {
        "intext": "Mathieu et al., 2011",
        "apa": "Mathieu, J. L., Price, P. N., Kiliccote, S., & Piette, M. A. (2011). Quantifying "
               "changes in building electricity use, with application to demand response. IEEE "
               "Transactions on Smart Grid, 2(3), 507–518. https://doi.org/10.1109/TSG.2011.2145010",
        "csl": {
            "type": "article-journal", "title": "Quantifying Changes in Building Electricity Use, "
            "With Application to Demand Response", "container-title": "IEEE Transactions on Smart Grid",
            "volume": "2", "issue": "3", "page": "507-518", "DOI": "10.1109/TSG.2011.2145010",
            "issued": {"date-parts": [[2011]]},
            "author": [{"family": "Mathieu", "given": "Johanna L."},
                       {"family": "Price", "given": "Phillip N."},
                       {"family": "Kiliccote", "given": "Sila"},
                       {"family": "Piette", "given": "Mary Ann"}],
        },
        "ris_type": "JOUR",
    },
    "zhang2016": {
        "intext": "Zhang et al., 2016",
        "apa": "Zhang, Y., Chen, W., Xu, R., & Black, J. (2016). A cluster-based method for "
               "calculating baselines for residential loads. IEEE Transactions on Smart Grid, "
               "7(5), 2368–2377. https://doi.org/10.1109/TSG.2015.2463755",
        "csl": {
            "type": "article-journal", "title": "A Cluster-Based Method for Calculating Baselines "
            "for Residential Loads", "container-title": "IEEE Transactions on Smart Grid",
            "volume": "7", "issue": "5", "page": "2368-2377", "DOI": "10.1109/TSG.2015.2463755",
            "issued": {"date-parts": [[2016]]},
            "author": [{"family": "Zhang", "given": "Yi"}, {"family": "Chen", "given": "Weiwei"},
                       {"family": "Xu", "given": "Rui"}, {"family": "Black", "given": "Jason"}],
        },
        "ris_type": "JOUR",
    },
    "koenker1978": {
        "intext": "Koenker & Bassett, 1978",
        "apa": "Koenker, R., & Bassett, G. (1978). Regression quantiles. Econometrica, 46(1), "
               "33–50. https://doi.org/10.2307/1913643",
        "csl": {
            "type": "article-journal", "title": "Regression Quantiles",
            "container-title": "Econometrica", "volume": "46", "issue": "1", "page": "33-50",
            "DOI": "10.2307/1913643", "issued": {"date-parts": [[1978]]},
            "author": [{"family": "Koenker", "given": "Roger"},
                       {"family": "Bassett", "given": "Gilbert"}],
        },
        "ris_type": "JOUR",
    },
    "dempster1977": {
        "intext": "Dempster et al., 1977",
        "apa": "Dempster, A. P., Laird, N. M., & Rubin, D. B. (1977). Maximum likelihood from "
               "incomplete data via the EM algorithm. Journal of the Royal Statistical Society: "
               "Series B (Methodological), 39(1), 1–22. "
               "https://doi.org/10.1111/j.2517-6161.1977.tb01600.x",
        "csl": {
            "type": "article-journal", "title": "Maximum Likelihood from Incomplete Data via the "
            "EM Algorithm", "container-title": "Journal of the Royal Statistical Society: Series B "
            "(Methodological)", "volume": "39", "issue": "1", "page": "1-22",
            "DOI": "10.1111/j.2517-6161.1977.tb01600.x", "issued": {"date-parts": [[1977]]},
            "author": [{"family": "Dempster", "given": "A. P."},
                       {"family": "Laird", "given": "N. M."}, {"family": "Rubin", "given": "D. B."}],
        },
        "ris_type": "JOUR",
    },
    "mclachlan2000": {
        "intext": "McLachlan & Peel, 2000",
        "apa": "McLachlan, G. J., & Peel, D. (2000). Finite mixture models. John Wiley & Sons. "
               "https://doi.org/10.1002/0471721182",
        "csl": {
            "type": "book", "title": "Finite Mixture Models", "publisher": "John Wiley & Sons",
            "publisher-place": "New York", "DOI": "10.1002/0471721182", "ISBN": "978-0-471-00626-8",
            "issued": {"date-parts": [[2000]]},
            "author": [{"family": "McLachlan", "given": "Geoffrey J."},
                       {"family": "Peel", "given": "David"}],
        },
        "ris_type": "BOOK",
    },
    "ashman1994": {
        "intext": "Ashman et al., 1994",
        "apa": "Ashman, K. A., Bird, C. M., & Zepf, S. E. (1994). Detecting bimodality in "
               "astronomical datasets. The Astronomical Journal, 108(6), 2348–2361. "
               "https://doi.org/10.1086/117248",
        "csl": {
            "type": "article-journal", "title": "Detecting bimodality in astronomical datasets",
            "container-title": "The Astronomical Journal", "volume": "108", "issue": "6",
            "page": "2348-2361", "DOI": "10.1086/117248", "issued": {"date-parts": [[1994]]},
            "author": [{"family": "Ashman", "given": "Keith A."},
                       {"family": "Bird", "given": "Christina M."},
                       {"family": "Zepf", "given": "Stephen E."}],
        },
        "ris_type": "JOUR",
    },
    "pedregosa2011": {
        "intext": "Pedregosa et al., 2011",
        "apa": "Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., "
               "Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., "
               "Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011). Scikit-learn: "
               "Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830.",
        "csl": {
            "type": "article-journal", "title": "Scikit-learn: Machine Learning in Python",
            "container-title": "Journal of Machine Learning Research", "volume": "12",
            "page": "2825-2830", "URL": "https://www.jmlr.org/papers/v12/pedregosa11a.html",
            "issued": {"date-parts": [[2011]]},
            "author": [{"family": "Pedregosa", "given": "Fabian"},
                       {"family": "Varoquaux", "given": "Gaël"},
                       {"family": "Gramfort", "given": "Alexandre"},
                       {"family": "Michel", "given": "Vincent"},
                       {"family": "Thirion", "given": "Bertrand"},
                       {"family": "Grisel", "given": "Olivier"},
                       {"family": "Blondel", "given": "Mathieu"},
                       {"family": "Prettenhofer", "given": "Peter"},
                       {"family": "Weiss", "given": "Ron"},
                       {"family": "Dubourg", "given": "Vincent"},
                       {"family": "Vanderplas", "given": "Jake"},
                       {"family": "Passos", "given": "Alexandre"},
                       {"family": "Cournapeau", "given": "David"},
                       {"family": "Brucher", "given": "Matthieu"},
                       {"family": "Perrot", "given": "Matthieu"},
                       {"family": "Duchesnay", "given": "Édouard"}],
        },
        "ris_type": "JOUR",
    },
    "kelly2015": {
        "intext": "Kelly & Knottenbelt, 2015",
        "apa": "Kelly, J., & Knottenbelt, W. (2015). The UK-DALE dataset, domestic "
               "appliance-level electricity demand and whole-house demand from five UK homes. "
               "Scientific Data, 2, 150007. https://doi.org/10.1038/sdata.2015.7",
        "csl": {
            "type": "article-journal", "title": "The UK-DALE dataset, domestic appliance-level "
            "electricity demand and whole-house demand from five UK homes",
            "container-title": "Scientific Data", "volume": "2", "page": "150007",
            "DOI": "10.1038/sdata.2015.7", "issued": {"date-parts": [[2015]]},
            "author": [{"family": "Kelly", "given": "Jack"},
                       {"family": "Knottenbelt", "given": "William"}],
        },
        "ris_type": "JOUR",
    },
    "murray2017": {
        "intext": "Murray et al., 2017",
        "apa": "Murray, D., Stankovic, L., & Stankovic, V. (2017). An electrical load measurements "
               "dataset of United Kingdom households from a two-year longitudinal study. "
               "Scientific Data, 4, 160122. https://doi.org/10.1038/sdata.2016.122",
        "csl": {
            "type": "article-journal", "title": "An electrical load measurements dataset of United "
            "Kingdom households from a two-year longitudinal study",
            "container-title": "Scientific Data", "volume": "4", "page": "160122",
            "DOI": "10.1038/sdata.2016.122", "issued": {"date-parts": [[2017]]},
            "author": [{"family": "Murray", "given": "David"},
                       {"family": "Stankovic", "given": "Lina"},
                       {"family": "Stankovic", "given": "Vladimir"}],
        },
        "ris_type": "JOUR",
    },
    "wilson2022": {
        "intext": "Wilson et al., 2022",
        "apa": "Wilson, E., Parker, A., Fontanini, A., Present, E., Reyna, J., Adhikari, R., "
               "Bianchi, C., CaraDonna, C., Dahlhausen, M., Kim, J., LeBar, A., Liu, L., "
               "Praprost, M., Zhang, L., DeWitt, P., Merket, N., Speake, A., Hong, T., Li, H., "
               "… Li, Q. (2022). End-use load profiles for the U.S. building stock: Methodology "
               "and results of model calibration, validation, and uncertainty quantification "
               "(NREL/TP-5500-80889). National Renewable Energy Laboratory. "
               "https://doi.org/10.2172/1854582",
        "csl": {
            "type": "report", "title": "End-Use Load Profiles for the U.S. Building Stock: "
            "Methodology and Results of Model Calibration, Validation, and Uncertainty "
            "Quantification", "number": "NREL/TP-5500-80889",
            "publisher": "National Renewable Energy Laboratory", "publisher-place": "Golden, CO",
            "DOI": "10.2172/1854582", "issued": {"date-parts": [[2022]]},
            "author": [{"family": "Wilson", "given": "Eric"}, {"family": "Parker", "given": "Andrew"},
                       {"family": "Fontanini", "given": "Anthony"},
                       {"family": "Present", "given": "Elaina"},
                       {"family": "Reyna", "given": "Janet"},
                       {"family": "Adhikari", "given": "Rajendra"},
                       {"family": "Bianchi", "given": "Carlo"},
                       {"family": "CaraDonna", "given": "Christopher"},
                       {"family": "Dahlhausen", "given": "Matthew"},
                       {"family": "Kim", "given": "Janghyun"},
                       {"family": "LeBar", "given": "Amy"}, {"family": "Liu", "given": "Lixi"},
                       {"family": "Praprost", "given": "Marlena"},
                       {"family": "Zhang", "given": "Liang"},
                       {"family": "DeWitt", "given": "Peter"},
                       {"family": "Merket", "given": "Noel"},
                       {"family": "Speake", "given": "Andrew"},
                       {"family": "Hong", "given": "Tianzhen"}, {"family": "Li", "given": "Han"},
                       {"family": "Li", "given": "Qu"}],
        },
        "ris_type": "RPRT",
    },
}

# Order of the reference list (APA = alphabetical by first author family name).
BIBLIOGRAPHY_ORDER = sorted(
    REFS, key=lambda k: (REFS[k]["csl"]["author"][0]["family"].lower(),
                         REFS[k]["csl"]["issued"]["date-parts"][0][0])
)


# =========================================================================
# IEEE reference-list rendering
# =========================================================================
# The venue is an IEEE conference, so the paper uses IEEE numeric style rather
# than APA: citations are bracketed numbers assigned in order of first use, and
# entries carry abbreviated author initials and no DOI URLs. Besides being the
# correct style, it is far more compact - the APA list with full DOI links ran
# to well over a page on its own, which a 4-page limit cannot absorb.
#
# The APA strings above are retained: they remain the human-readable fallback
# inside the Zotero field result, and the .ris export is unaffected.

# Common IEEE journal-title abbreviations, applied to the titles actually cited.
_ABBREV = {
    "IEEE Transactions on Industrial Informatics": "IEEE Trans. Ind. Informat.",
    "IEEE Transactions on Smart Grid": "IEEE Trans. Smart Grid",
    "Proceedings of the IEEE": "Proc. IEEE",
    "Econometrica": "Econometrica",
    "Journal of the Royal Statistical Society: Series B (Methodological)":
        "J. R. Stat. Soc. B",
    "The Astronomical Journal": "Astron. J.",
    "Journal of Machine Learning Research": "J. Mach. Learn. Res.",
    "Scientific Data": "Sci. Data",
    "Energies": "Energies",
}


def _initials(given: str) -> str:
    """'Peter' -> 'P.';  'Jean-Luc' -> 'J.-L.';  'Yi' -> 'Y.'"""
    parts = [q for q in given.replace("-", " - ").split() if q]
    out = []
    for q in parts:
        out.append("-" if q == "-" else f"{q[0]}.")
    return "".join(o if o == "-" else o + " " for o in out).replace(" -", "-").strip()


def _ieee_authors(authors: list[dict]) -> str:
    """IEEE lists up to six authors, then 'et al.' after the first."""
    names = [f"{_initials(a['given'])} {a['family']}" for a in authors]
    if len(names) > 6:
        return f"{names[0]} et al."
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return " and ".join(names)      # IEEE takes no comma before "and" for two
    return ", ".join(names[:-1]) + ", and " + names[-1]


def ieee_entry(key: str) -> str:
    """One IEEE-style reference-list entry, without its leading number."""
    c = REFS[key]["csl"]
    year = c["issued"]["date-parts"][0][0]
    who = _ieee_authors(c["author"])
    kind = c.get("type")

    if kind == "book":
        place = c.get("publisher-place")
        where = f"{place}: {c['publisher']}" if place else c["publisher"]
        return f"{who}, {c['title']}. {where}, {year}."

    if kind == "report":
        bits = [f"{who}, “{c['title']},”", c["publisher"]]
        if c.get("number"):
            bits.append(f"Rep. {c['number']}")
        bits.append(f"{year}.")
        return " ".join(bits[:1]) + " " + ", ".join(bits[1:-1]) + f", {year}."

    journal = c.get("container-title", "")
    journal = _ABBREV.get(journal, journal)
    bits = [f"{who}, “{c['title']},” {journal}"]
    if c.get("volume"):
        bits.append(f"vol. {c['volume']}")
    if c.get("issue"):
        bits.append(f"no. {c['issue']}")
    if c.get("page"):
        pages = c["page"].replace("-", "–")
        bits.append(f"pp. {pages}" if "–" in pages else f"p. {pages}")
    bits.append(f"{year}.")
    return ", ".join(bits)


def _ris_authors(rec) -> list[str]:
    return [f"AU  - {a['family']}, {a['given']}" for a in rec["csl"]["author"]]


def write_ris(path: Path) -> Path:
    """Export every reference as RIS for import into Zotero."""
    lines: list[str] = []
    for key in BIBLIOGRAPHY_ORDER:
        rec = REFS[key]
        c = rec["csl"]
        lines.append(f"TY  - {rec['ris_type']}")
        lines += _ris_authors(rec)
        lines.append(f"PY  - {c['issued']['date-parts'][0][0]}")
        lines.append(f"TI  - {c['title']}")
        if c.get("container-title"):
            lines.append(f"T2  - {c['container-title']}")
            lines.append(f"JO  - {c['container-title']}")
        if c.get("volume"):
            lines.append(f"VL  - {c['volume']}")
        if c.get("issue"):
            lines.append(f"IS  - {c['issue']}")
        if c.get("page"):
            pages = c["page"].split("-")
            lines.append(f"SP  - {pages[0]}")
            if len(pages) > 1:
                lines.append(f"EP  - {pages[1]}")
        if c.get("publisher"):
            lines.append(f"PB  - {c['publisher']}")
        if c.get("publisher-place"):
            lines.append(f"CY  - {c['publisher-place']}")
        if c.get("number"):
            lines.append(f"M1  - {c['number']}")
        if c.get("ISBN"):
            lines.append(f"SN  - {c['ISBN']}")
        if c.get("DOI"):
            lines.append(f"DO  - {c['DOI']}")
            lines.append(f"UR  - https://doi.org/{c['DOI']}")
        elif c.get("URL"):
            lines.append(f"UR  - {c['URL']}")
        lines.append("ER  - ")
        lines.append("")
    text = "\r\n".join(lines)
    path.write_text(text, encoding="utf-8")
    return path
