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
    with open(REPORT_PATH, "w") as report_file:
        json.dump(validation_reports, report_file, indent=4)

    # Salva o relatório completo em formato TXT
    with open("validation_report.txt", "w") as txt_file:
        for report in validation_reports:
            txt_file.write(f"Arquivo: {report['file']}\n")
            if "error" in report:
                txt_file.write(f"  Erro: {report['error']}\n")
            else:
                for result in report["results"]:
                    txt_file.write(f"  IfcProject: {result.get('IfcProject', 'N/A')}\n")
                    txt_file.write(f"  IfcBuilding: {result.get('IfcBuilding', 'N/A')}\n")
                    txt_file.write(f"  IfcBuildingStorey: {result.get('IfcBuildingStorey', 'N/A')}\n")
                    txt_file.write(f"  IfcSpace: {result.get('IfcSpace', 'N/A')}\n")
                    txt_file.write(f"  Coordenadas: {result.get('Coordenadas', 'N/A')}\n")
                    txt_file.write(f"  Disciplinas: {result.get('Disciplinas', 'N/A')}\n")
                    txt_file.write(f"  Especificações Técnicas: {result.get('Especificações Técnicas', 'N/A')}\n")
                    # Loop para os novos campos Ifc
                    for field in additional_fields:
                        txt_file.write(f"  {field}: {result.get(field, 'Ausente')}\n")
            txt_file.write("\n")

    # Salva o relatório completo em formato CSV
    with open("validation_report.csv", "w", newline="") as csv_file:
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
                        result.get("IfcProject", "N/A"),
                        result.get("IfcBuilding", "N/A"),
                        result.get("IfcBuildingStorey", "N/A"),
                        result.get("IfcSpace", "N/A"),
                        result.get("Coordenadas", "N/A"),
                        result.get("Disciplinas", "N/A"),
                        result.get("Especificações Técnicas", "N/A")
                    ]
                    row.extend(result.get(field, "Ausente") for field in additional_fields)
                    csv_writer.writerow(row)

import os
print(f"Diretório atual: {os.getcwd()}")
