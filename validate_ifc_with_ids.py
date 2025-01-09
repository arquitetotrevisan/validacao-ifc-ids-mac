import os
import json
import csv
from lxml import etree
import ifcopenshell
import pyproj

try:
    print("ifcopenshell importado com sucesso!")
except ImportError as e:
    print(f"Erro ao importar ifcopenshell: {str(e)}")
    exit(1)

# Caminhos para os arquivos de relatório diretamente no diretório raiz
IDS_PATH = "./ids.xsd"
TXT_REPORT_PATH = "./validation_report.txt"
JSON_REPORT_PATH = "./validation_report.json"
CSV_REPORT_PATH = "./validation_report.csv"

# Campos adicionais para validação
additional_fields = [
    "IfcWall", "IfcSlab", "IfcWindow", "IfcDoor", "IfcBeam", "IfcColumn", "IfcStair", "IfcRoof"
]

# Função para validar a presença dos campos no arquivo IFC
def validate_ifc_with_ids(file, ids_root):
    try:
        ifc_file = ifcopenshell.open(file)
        project = ifc_file.by_type("IfcProject")
        building = ifc_file.by_type("IfcBuilding")
        
        # Obter valores principais de IfcProject
        project_content = project[0].Name if project and hasattr(project[0], "Name") else "Ausente"

        # Obter valores principais de IfcBuilding
        building_content = building[0].Name if building and hasattr(building[0], "Name") else "Ausente"
        
        building_storey = ifc_file.by_type("IfcBuildingStorey")
        spaces = ifc_file.by_type("IfcSpace")
        coordinates = get_coordinates(ifc_file)
        
        # Conta os elementos dos campos adicionais
        additional_data = {field: len(ifc_file.by_type(field)) for field in additional_fields}

        result = {
            "file": file,
            "results": [{
                "IfcProject": project_content,
                "IfcBuilding": building_content,
                "IfcBuildingStorey": "Presente" if building_storey else "Ausente",
                "IfcSpace": f"{len(spaces)} espaços encontrados" if spaces else "Ausente",
                "Coordenadas": coordinates,
            }]
        }

        # Adiciona os campos adicionais
        for field, count in additional_data.items():
            result["results"][0][field] = f"{count} encontrados" if count > 0 else "Ausente"

        # Adiciona o endereço postal
        postal_address = get_postal_address(ifc_file)
        result["results"][0]["IfcPostalAddress"] = postal_address
        
        return result
    except Exception as e:
        return {"file": file, "error": f"Erro ao processar {file}: {str(e)}"}

# Função para obter coordenadas em formato legível
def get_coordinates(ifc_file):
    try:
        ifc_site = ifc_file.by_type("IfcSite")
        if ifc_site:
            site = ifc_site[0]
            if hasattr(site, "RefLatitude") and hasattr(site, "RefLongitude"):
                lat = site.RefLatitude
                lon = site.RefLongitude
                elevation = getattr(site, "RefElevation", "0.0")
                lat_dec = latitude_to_decimal(lat)
                lon_dec = longitude_to_decimal(lon)
                return f"Latitude: {lat_dec}, Longitude: {lon_dec}, Elevação: {elevation}m"
    except Exception as e:
        return f"Erro ao processar coordenadas para o arquivo atual: {str(e)}"
    return "Coordenadas não encontradas"

# Funções para conversão de latitude/longitude
def latitude_to_decimal(lat):
    return sum(x / 60 ** i for i, x in enumerate(lat)) if lat else "Inválido"

def longitude_to_decimal(lon):
    return sum(x / 60 ** i for i, x in enumerate(lon)) if lon else "Inválido"

# Verifica o campo IfcPostalAddress
def get_postal_address(ifc_file):
    try:
        addresses = ifc_file.by_type("IfcPostalAddress")
        if addresses:
            address = addresses[0]
            address_lines = getattr(address, "AddressLines", [])
            postal_code = getattr(address, "PostalCode", "Não especificado")
            city = getattr(address, "Town", "Não especificado")
            return f"{', '.join(address_lines)}, {city}, CEP: {postal_code}" if address_lines else "Endereço não especificado"
    except Exception as e:
        return f"Erro ao processar endereço: {str(e)}"
    return "Endereço não encontrado"

# Função principal
def main():
    print("Iniciando a validação e geração de relatórios...")

    if not os.access('.', os.W_OK):
        print(f"Não é possível escrever no diretório atual ({os.getcwd()}). Verifique as permissões.")
        return  # Finaliza o programa se não puder escrever
    else:
        print("Permissão de escrita confirmada.")

    # Carrega o IDS
    with open(IDS_PATH, "r") as f:
        ids_root = etree.parse(f).getroot()

    # Valida todos os arquivos IFC no diretório
    validation_reports = []
    for file in os.listdir("."):
        if file.endswith(".ifc"):
            print(f"Validando: {file}")
            validation_reports.append(validate_ifc_with_ids(file, ids_root))

    # Salva o relatório JSON
    print("Salvando relatório JSON...")
    with open(JSON_REPORT_PATH, "w") as json_file:
        json.dump(validation_reports, json_file, indent=4)

    # Salva o relatório TXT
    print("Salvando relatório TXT...")
    with open(TXT_REPORT_PATH, "w") as txt_file:
        for report in validation_reports:
            txt_file.write(f"Arquivo: {report['file']}\n")
            if "error" in report:
                txt_file.write(f"  Erro: {report['error']}\n")
            else:
                for result in report["results"]:
                    for key, value in result.items():
                        if key == "IfcPostalAddress":
                            txt_file.write(f"  Endereço: {value}\n")
                        else:
                            txt_file.write(f"  {key}: {value}\n")


    # Salva o relatório CSV
    print("Salvando relatório CSV...")
    with open(CSV_REPORT_PATH, "w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        headers = ["Arquivo", "IfcProject", "IfcBuilding", "IfcBuildingStorey", "IfcSpace", "Coordenadas", "IfcPostalAddress"] + additional_fields
        csv_writer.writerow(headers)
        for report in validation_reports:
            if "error" in report:
                csv_writer.writerow([report["file"], report["error"]] + [""] * (len(headers) - 2))
            else:
                for result in report["results"]:
                    row = [report["file"]]
                    row.extend(result.get(field, "Ausente") for field in headers[1:])
                    csv_writer.writerow(row)

if __name__ == "__main__":
    main()
