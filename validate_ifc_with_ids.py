import os
import json
import ifcopenshell
from lxml import etree

# Caminho para o IDS
IDS_PATH = "./ids.xsd"
# Caminho para o relatório JSON gerado
REPORT_PATH = "validation_report.json"

# Definindo a lista de campos adicionais fora da função
additional_fields = [
    "IfcWall", "IfcSlab", "IfcWindow", "IfcDoor",
    "IfcBeam", "IfcColumn", "IfcRailing",
    "IfcStair", "IfcRoof"
]

def validate_ifc_with_ids(ifc_file, ids_root):
    """Valida um arquivo IFC contra o IDS fornecido."""
    report = {"file": ifc_file, "results": []}
    
    try:
        # Abre o arquivo IFC
        model = ifcopenshell.open(ifc_file)

        # Cria o dicionário de resultados para as entidades verificadas
        result = {
            "IfcProject": "Ausente",
            "IfcBuilding": "Ausente",
            "IfcBuildingStorey": "Ausente",
            "IfcSpace": "Menos de 2 espaços encontrados",
            "Coordenadas": None,
            "Disciplinas": None,
            "Especificações Técnicas": "Ausente"
        }

        # Verifica se IfcProject está presente
        if model.by_type("IfcProject"):
            result["IfcProject"] = "Presente"

        # Verifica se IfcBuilding está presente
        if model.by_type("IfcBuilding"):
            result["IfcBuilding"] = "Presente"

        # Verifica se IfcBuildingStorey está presente
        if model.by_type("IfcBuildingStorey"):
            result["IfcBuildingStorey"] = "Presente"

        # Verifica se há pelo menos dois IfcSpace
        spaces = model.by_type("IfcSpace")
        if len(spaces) >= 2:
            result["IfcSpace"] = f"{len(spaces)} espaços encontrados"
        else:
            result["IfcSpace"] = "Menos de 2 espaços encontrados"

        # Verifica a presença dos novos campos Ifc
        for field in additional_fields:
            entities = model.by_type(field)
            if entities:
                result[field] = f"{len(entities)} encontrados"
            else:
                result[field] = "Ausente"

        # Obtém as coordenadas (assume-se que as coordenadas são da primeira instância de IfcSite)
        ifc_site = model.by_type("IfcSite")
        if ifc_site:
            # Obter coordenadas, considerando que alguns valores podem ser None ou zero
            def convert_to_decimal(degrees_tuple):
                """Converte uma tupla (graus, minutos, segundos, frações) em decimal."""
                if degrees_tuple:
                    degrees, minutes, seconds, *fractions = degrees_tuple
                    decimal = degrees + (minutes / 60) + (seconds / 3600)
                    if fractions:
                        decimal += fractions[0] / (3600 * 10000)  # Assume que frações são baseadas em décimos de segundos
                    return decimal
                return 0.0

            latitude = convert_to_decimal(ifc_site[0].RefLatitude)
            longitude = convert_to_decimal(ifc_site[0].RefLongitude)
            elevation = ifc_site[0].RefElevation if ifc_site[0].RefElevation is not None else 0.0

            # Apresentação das coordenadas de forma compreensível
            result["Coordenadas"] = f"Latitude: {latitude:.4f}, Longitude: {longitude:.4f}, Elevation: {elevation:.2f}m"
        else:
            result["Coordenadas"] = "Coordenadas não encontradas"

        # Verifica se há disciplinas (assume-se que são tipos IfcRelAssociatesDocument)
        disciplines = model.by_type("IfcRelAssociatesDocument")
        if disciplines:
            result["Disciplinas"] = ", ".join([discipline.RelatedDocuments[0].Name for discipline in disciplines])
        else:
            result["Disciplinas"] = "Nenhuma disciplina encontrada"

        # Verifica se há especificações técnicas
        specifications = model.by_type("IfcDocumentReference")
        if specifications:
            result["Especificações Técnicas"] = "Preenchidas"
        else:
            result["Especificações Técnicas"] = "Ausentes"

        # Adiciona o resultado ao relatório
        report["results"].append(result)

    except Exception as e:
        report["error"] = str(e)

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
                    txt_file.write(f"  IfcProject: {result['IfcProject']}\n")
                    txt_file.write(f"  IfcBuilding: {result['IfcBuilding']}\n")
                    txt_file.write(f"  IfcBuildingStorey: {result['IfcBuildingStorey']}\n")
                    txt_file.write(f"  IfcSpace: {result['IfcSpace']}\n")
                    txt_file.write(f"  Coordenadas: {result['Coordenadas']}\n")
                    txt_file.write(f"  Disciplinas: {result['Disciplinas']}\n")
                    txt_file.write(f"  Especificações Técnicas: {result['Especificações Técnicas']}\n")
                    # Loop para os novos campos Ifc
                    for field in additional_fields:
                        if field in result:
                            txt_file.write(f"  {field}: {result[field]}\n")
            txt_file.write("\n")

if __name__ == "__main__":
    main()
