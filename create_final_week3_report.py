#!/usr/bin/env python3
"""Build the final APA 7 Week 3 report as an eight-page DOCX."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "deliverables" / "MSAI699_Week3_Model_Selection_Tuning_Explainability_Kalirajan_Natarajan.docx"
FIG = ROOT / "results" / "figures"
REPOSITORY_URL = "https://github.com/kalirajann/auditable-model-risk-retrieval"


def page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    text = OxmlElement("w:instrText")
    text.set(qn("xml:space"), "preserve")
    text.text = "PAGE"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, text, end])


def hyperlink(paragraph, text, url):
    relationship = paragraph.part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), relationship)
    run = OxmlElement("w:r")
    properties = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    properties.extend([color, underline])
    value = OxmlElement("w:t")
    value.text = text
    run.extend([properties, value])
    link.append(run)
    paragraph._p.append(link)


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=55, start=70, bottom=55, end=70):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_borders(table, color="808080", size="5"):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = borders.find(qn(f"w:{edge}"))
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:color"), color)


def keep_row(row):
    tr_pr = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    tr_pr.append(cant_split)


def body(doc, text, indent=True):
    p = doc.add_paragraph(style="Body")
    p.paragraph_format.first_line_indent = Inches(0.5) if indent else Inches(0)
    p.add_run(text)
    return p


def heading(doc, text, level=1):
    p = doc.add_paragraph(style="Heading 1" if level == 1 else "Heading 2")
    p.add_run(text)
    return p


def note(doc, label, text):
    p = doc.add_paragraph(style="Body")
    p.paragraph_format.first_line_indent = Inches(0)
    r = p.add_run(label)
    r.bold = True
    p.add_run(text)
    return p


def table(doc, headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, width in enumerate(widths):
        t.columns[i].width = Inches(width)
    for i, value in enumerate(headers):
        cell = t.rows[0].cells[i]
        set_cell_shading(cell, "D9EAF2")
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing = 1
        r = p.add_run(value)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(9)
    keep_row(t.rows[0])
    for row_values in rows:
        cells = t.add_row().cells
        for i, value in enumerate(row_values):
            cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cells[i].paragraphs[0]
            p.paragraph_format.line_spacing = 1
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(value))
            r.font.name = "Arial"
            r.font.size = Pt(9)
            if i > 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_cell_margins(cells[i])
        keep_row(t.rows[-1])
    set_borders(t)
    return t


def figure(doc, path, width, number, title):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(path), width=Inches(width))
    c = doc.add_paragraph(style="Caption")
    c.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = c.add_run(f"Figure {number}\n")
    r.bold = True
    i = c.add_run(title)
    i.italic = True


doc = Document()
section = doc.sections[0]
section.page_width = Inches(8.5)
section.page_height = Inches(11)
section.top_margin = Inches(1)
section.bottom_margin = Inches(1)
section.left_margin = Inches(1)
section.right_margin = Inches(1)
section.header_distance = Inches(0.5)
page_number(section.header.paragraphs[0])

styles = doc.styles
normal = styles["Normal"]
normal.font.name = "Arial"
normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
normal.font.size = Pt(11)
normal.paragraph_format.line_spacing = 2
normal.paragraph_format.space_after = Pt(0)

body_style = styles.add_style("Body", 1)
body_style.base_style = normal
body_style.font.name = "Arial"
body_style._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
body_style.font.size = Pt(11)
body_style.paragraph_format.line_spacing = 2
body_style.paragraph_format.space_after = Pt(0)

for name, align in (("Heading 1", WD_ALIGN_PARAGRAPH.CENTER), ("Heading 2", WD_ALIGN_PARAGRAPH.LEFT)):
    s = styles[name]
    s.font.name = "Arial"
    s._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    s.font.size = Pt(11)
    s.font.bold = True
    s.font.color.rgb = None
    s.paragraph_format.alignment = align
    s.paragraph_format.line_spacing = 2
    s.paragraph_format.space_before = Pt(0)
    s.paragraph_format.space_after = Pt(0)
    s.paragraph_format.keep_with_next = True

caption = styles["Caption"]
caption.font.name = "Arial"
caption._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
caption.font.size = Pt(10)
caption.font.color.rgb = None
caption.paragraph_format.line_spacing = 1
caption.paragraph_format.space_after = Pt(2)

reference = styles.add_style("Reference", 1)
reference.font.name = "Arial"
reference._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
reference.font.size = Pt(10)
reference.paragraph_format.line_spacing = 1.15
reference.paragraph_format.left_indent = Inches(0.5)
reference.paragraph_format.first_line_indent = Inches(-0.5)
reference.paragraph_format.space_after = Pt(3)

# Page 1: title page
doc.add_paragraph().paragraph_format.space_after = Pt(78)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.line_spacing = 2
r = p.add_run("Local Model Selection, Tuning, and Explainability for\nAuditable Bank Model-Risk Retrieval")
r.bold = True
r.font.name = "Arial"
r.font.size = Pt(11)
doc.add_paragraph().paragraph_format.space_after = Pt(34)
for line in (
    "Kalirajan Natarajan",
    "University of the Cumberlands",
    "MSAI 699: Capstone Project",
    "Week 3 Assignment: Model Selection and Baseline Implementation",
    "November 6, 2026",
):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing = 2
    p.add_run(line)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.line_spacing = 2
r = p.add_run("Public project repository:\n")
r.bold = True
hyperlink(p, REPOSITORY_URL, REPOSITORY_URL)

doc.add_page_break()

# Page 2: abstract
heading(doc, "Abstract")
body(doc, "This report documents Week 3 of the capstone project, Auditable Long-Memory Retrieval for Bank Model Risk Management. The project studies whether a local retrieval-augmented generation system can locate the correct model-risk evidence, respect document dates and status, cite its evidence, and abstain when the evidence is missing. The Auditable Model Risk Evidence Benchmark (AMREB) contains 72 synthetic documents and 120 questions covering six banking model families. A transparent TF-IDF retriever was retained as the lower-bound comparator. The selected AI baseline uses the local nomic-embed-text model for semantic retrieval and qwen3.5:9b-q4_K_M as a fixed grounded reader. A random-forest feature ranker was then tuned with Optuna, and its behavior was inspected with SHAP. On the 30-question development split, dense retrieval achieved perfect Hit Rate and Recall at 5 with mean reciprocal rank (MRR) of 0.8125. The tuned ranker improved MRR to 0.9583 while retaining a Hit Rate at 5 of 1.0000. The reader achieved 1.0000 abstention accuracy and 0.9583 citation hit rate. These are development results, not final generalization claims; the test split remains frozen. The work establishes a reproducible, privacy-conscious baseline for later deployment and evaluation.")
note(doc, "Keywords: ", "bank model risk, retrieval-augmented generation, Optuna, SHAP, explainable AI")

doc.add_page_break()

# Page 3: introduction
heading(doc, "Local Model Selection, Tuning, and Explainability for Auditable Bank Model-Risk Retrieval")
heading(doc, "Introduction", 2)
body(doc, "The capstone topic is Auditable Long-Memory Retrieval for Bank Model Risk Management. A bank AI assistant must retrieve the correct model and version, respect the date when evidence became effective, cite its sources, and abstain when support is absent. The system therefore separates retrieval, ranking, and answer generation so each stage can be measured.")
body(doc, "This week selects a model, establishes a benchmark, runs initial experiments, documents results, and identifies improvements. The primary AI baseline is nomic-embed-text semantic retrieval. Qwen 3.5 is a fixed, evidence-bound reader; TF-IDF is a lower-bound comparator. The Optuna-tuned random forest is an improvement experiment, not the baseline.")
body(doc, "The design keeps the evidence path visible. It supports the NIST principles of validity, accountability, transparency, explainability, privacy, and managed bias through local inference, versioned data, fixed splits, citations, abstention, saved parameters, and feature explanations (Tabassi, 2023). It does not claim production readiness or regulatory approval.")
heading(doc, "Research Questions", 2)
body(doc, "The study asks whether semantic retrieval improves lexical ranking, whether an explainable ranker improves evidence order without losing recall, which features drive its decisions, and whether a local reader cites and abstains correctly.")

# Page 4: data and models
heading(doc, "Dataset, Models, and Baseline Architecture")
heading(doc, "AMREB Dataset", 2)
body(doc, "AMREB version 1.0.0 contains 72 synthetic model-risk documents and 120 balanced questions across six banking model families and five reasoning categories. The split is 60 training, 30 development, and 30 test questions. Only training and development data were used; the test set was not accessed.")
heading(doc, "Selected Local Models", 2)
table(doc,
      ("Component", "Selection", "Role and reason"),
      (
          ("Lower bound", "TF-IDF + cosine", "Transparent lexical comparator; no learned semantics."),
          ("AI baseline", "nomic-embed-text", "137M-class local embedding model for semantic retrieval (Nussbaum et al., 2024)."),
          ("Grounded reader", "qwen3.5:9b-q4_K_M", "Local 9B quantized reader; answers only from supplied evidence."),
          ("Improvement", "Random forest", "Ranks candidate documents from lexical, dense, temporal, and metadata features."),
      ),
      (1.15, 1.75, 3.6))
body(doc, "Nomic Embed was selected because retrieval is central, it runs locally, and it has published reproducibility artifacts (Nussbaum et al., 2024). Exact Ollama identifiers were recorded: nomic-embed-text:latest (0a109f422b47) and qwen3.5:9b-q4_K_M (56671c2ab938).")
body(doc, "The random-forest ranker models nonlinear feature interactions (Breiman, 2001). Its features cover dense and lexical similarity, token overlap, model-ID match, authority, status, and effective date. Reader fluency is evaluated separately because it cannot reliably repair missing evidence.")

# Page 5: tools and selection
heading(doc, "Tuning, Explainability, and Experiment Tracking")
heading(doc, "Tuning Options", 2)
body(doc, "GridSearchCV exhaustively tests a specified grid but becomes costly as the grid grows (scikit-learn developers, n.d.). Hyperopt supports adaptive and distributed search. Optuna provides flexible spaces, trial records, and pruning (Akiba et al., 2019).")
body(doc, "Optuna was selected for the mixed search space and limited local budget. Thirty seeded trials tuned five random-forest settings. The best values were 220 trees, depth 3, minimum leaf size 5, feature fraction 0.7, and balanced-subsample weighting. Shallow trees also limit unnecessary complexity.")
heading(doc, "Explainability Options", 2)
body(doc, "LIME fits a simple local model around one prediction, but its result depends on sampled neighbors (Ribeiro et al., 2016). SHAP assigns feature contributions in a Shapley-value framework (Lundberg & Lee, 2017). SHAP was selected because TreeExplainer directly supports the random forest and produces local and global explanations.")
heading(doc, "Experiment Tracking", 2)
body(doc, "Weights & Biases can log configurations, metrics, runs, and artifacts for team-scale studies. It was not used because these local notebooks already save versioned parameters, metrics, details, figures, and artifacts. It can be added when runs or collaborators increase.")
note(doc, "Selection summary. ", "Optuna is used for tuning, SHAP is used for explaining the feature ranker, and local JSON/CSV artifacts are used for experiment tracking in this week.")

# Page 6: implementation and results
heading(doc, "Implementation and Experimental Results")
heading(doc, "Reproducible Notebook Workflow", 2)
body(doc, "Five notebooks cover dataset validation, dense retrieval, the grounded reader, Optuna tuning, and SHAP comparison. Seeds, exact models, checksums, frozen splits, and saved outputs support repeatability. All notebooks completed without cell errors.")
table(doc,
      ("Method", "Hit@5", "Recall@5", "Precision@5", "MRR"),
      (
          ("TF-IDF comparator", "1.0000", "0.9583", "0.2833", "0.6174"),
          ("Nomic dense baseline", "1.0000", "1.0000", "0.3000", "0.8125"),
          ("Optuna-tuned ranker", "1.0000", "0.9792", "0.2917", "0.9583"),
      ),
      (2.45, 0.85, 0.9, 0.95, 0.85))
note(doc, "Note. ", "Retrieval metrics use the 24 answerable development questions; six abstention questions are excluded. Top-k = 5.")
figure(doc, FIG / "all_model_comparison.png", 4.85, 1, "Development-set retrieval comparison")
body(doc, "Dense retrieval increased MRR by 0.1951 over TF-IDF. The tuned ranker added 0.1458, but Recall at 5 fell from 1.0000 to 0.9792. Better ordering does not justify losing synthesis evidence; later work should use multi-objective tuning or preserve high-recall dense candidates before reranking.")

# Page 7: explanations, reader, ethics, conclusion
heading(doc, "Explainability, Reader Results, and Conclusions")
figure(doc, FIG / "shap_summary.png", 4.65, 2, "Mean absolute SHAP contribution by ranker feature")
body(doc, "SHAP ranked token overlap, dense similarity, and lexical similarity highest. Effective date and model-ID match also contributed. Textual similarity still dominates governance signals, so later experiments should test stronger temporal and authority constraints.")
body(doc, "The Qwen reader achieved 1.0000 abstention accuracy, 0.9583 citation hit rate, 1.0000 retrieval-grounded citation rate, and 2.4483-second average latency. These are synthetic development results, not evidence of performance on confidential records, noisy OCR, access controls, or adversarial prompts.")
heading(doc, "Ethical and Maintainability Considerations", 2)
body(doc, "Synthetic data protects confidential information but cannot prove fairness or safety. Production requires access controls, encryption, audit logs, retention rules, prompt-injection defenses, human review, and evaluation across user groups. Citations and abstention must be monitored; SHAP is not causal proof. Models, data, metrics, and dependencies must be versioned and revalidated.")
heading(doc, "Conclusion", 2)
body(doc, "Nomic Embed is the baseline, Qwen 3.5 is the constrained reader, TF-IDF is the lower bound, and the Optuna-tuned random forest is the explainable improvement. Ranking improved, but the small recall loss must be fixed before using the frozen test set. Later FastAPI deployment will preserve evidence, citation, abstention, and audit controls.")

doc.add_page_break()

# Page 8: references
heading(doc, "References")
references = [
    [("Akiba, T., Sano, S., Yanase, T., Ohta, T., & Koyama, M. (2019). Optuna: A next-generation hyperparameter optimization framework. In ", False), ("Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining", True), (" (pp. 2623–2631). Association for Computing Machinery. https://doi.org/10.1145/3292500.3330701", False)],
    [("Breiman, L. (2001). Random forests. ", False), ("Machine Learning, 45", True), (", 5–32. https://doi.org/10.1023/A:1010933404324", False)],
    [("Hyperopt developers. (n.d.). ", False), ("Hyperopt documentation", True), (". Retrieved November 6, 2026, from https://hyperopt.github.io/hyperopt/", False)],
    [("Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. ", False), ("Advances in Neural Information Processing Systems, 30", True), (". https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html", False)],
    [("Nussbaum, Z., Morris, J. X., Duderstadt, B., & Mulyar, A. (2024). ", False), ("Nomic Embed: Training a reproducible long context text embedder", True), (" [Technical report]. Nomic AI. https://static.nomic.ai/reports/2024_Nomic_Embed_Text_Technical_Report.pdf", False)],
    [("Ollama. (2026). ", False), ("Qwen 3.5", True), (" [Computer software]. https://ollama.com/library/qwen3.5", False)],
    [("Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). ‘Why should I trust you?’: Explaining the predictions of any classifier. In ", False), ("Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining", True), (" (pp. 1135–1144). Association for Computing Machinery. https://doi.org/10.1145/2939672.2939778", False)],
    [("scikit-learn developers. (n.d.). ", False), ("GridSearchCV", True), (". In scikit-learn documentation. Retrieved November 6, 2026, from https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html", False)],
    [("Tabassi, E. (2023). ", False), ("Artificial intelligence risk management framework (AI RMF 1.0)", True), (" (NIST AI 100-1). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.AI.100-1", False)],
    [("Weights & Biases. (n.d.). ", False), ("W&B Models documentation", True), (". Retrieved November 6, 2026, from https://docs.wandb.ai/models/", False)],
]
for segments in references:
    p = doc.add_paragraph(style="Reference")
    for value, italic in segments:
        r = p.add_run(value)
        r.italic = italic

doc.core_properties.title = "Local Model Selection, Tuning, and Explainability for Auditable Bank Model-Risk Retrieval"
doc.core_properties.author = "Kalirajan Natarajan"
doc.core_properties.subject = "MSAI 699 Week 3 Assignment"
OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print(OUT)
