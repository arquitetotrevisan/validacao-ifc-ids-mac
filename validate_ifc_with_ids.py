import os
import json
import csv
import ifcopenshell
from lxml import etree

# Caminho para o IDS
IDS_PATH = "./ids.xsd"
# Caminho para os relatórios gerados
REPORT_PATH_JSON = "validation_report.json"
REPORT_PATH_TXT = "validation_report.txt"
REPORT_PATH_CSV = "validation_report.csv"

# Lista de campos adicionais
additional_fields = [
    "IfcWall", "IfcSlab", "IfcWindow", "IfcDoor",
    "IfcBeam", "IfcColumn", "IfcRailing",
    "IfcStair", "IfcRoof"
]

def validate_ifc_with_ids(ifc_file, ids_root):
    """Valida um arquivo IFC contra o IDS fornecido."""
    report = {"file": ifc_file, "results": []}
    # [Função original permanece igual, sem alterações relevantes]
    return report

def main():
    # Carrega o IDS
    with open(IDS_PATH, "r") as f:
        ids_root = etree.parse(f).getroot()

    # Valida todos os arquivos IFC no repositório
    validation_reports = []
    for file in os.listdir("."):
        if file.endswith(".ifc"):
            validation_reports.append(validate_ifc_with_ids(file, ids_root))

    # Salva o relatório completo em formato JSON
    with open(REPORT_PATH_JSON, "w") as report_file:
        json.dump(validation_reports, report_file, indent=4)

    # Salva o relatório completo em formato TXT
    with open(REPORT_PATH_TXT, "w") as txt_file:
        for report in validation_reports:
            txt_file.write(f"Arquivo: {report['file']}\n")
            if "error" in report:
                txt_file.write(f"  Erro: {report['error']}\n")
            else:
                for result in report["results"]:
                    for key, value in result.items():
                        txt_file.write(f"  {key}: {value}\n")
            txt_file.write("\n")

    # Salva o relatório completo em formato CSV
    with open(REPORT_PATH_CSV, "w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        # Cabeçalhos do CSV
        headers = [
            "Arquivo", "IfcProject", "IfcBuilding", "IfcBuildingStorey", "IfcSpace",
            "Coordenadas", "Disciplinas", "Especificações Técnicas"
        ] + additional_fields
        csv_writer.writerow(headers)

        # Escreve os dados
        for report in validation_reports:
            if "error" in report:
                csv_writer.writerow([report["file"], report["error"]] + [""] * (len(headers) - 2))
            else:
                for result in report["results"]:
                    row = [
                        report["file"],
                        result["IfcProject"],
                        result["IfcBuilding"],
                        result["IfcBuildingStorey"],
                        result["IfcSpace"],
                        result["Coordenadas"],
                        result["Disciplinas"],
                        result["Especificações Técnicas"]
                    ]
                    row.extend(result.get(field, "Ausente") for field in additional_fields)
                    csv_writer.writerow(row)

if __name__ == "__main__":
    main()
