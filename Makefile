# Nombre de la imagen
IMAGE_NAME=quant-drl-web
IMAGE_TAG=latest
TAR_FILE=$(IMAGE_NAME).tar

# GitHub Container Registry
GITHUB_USER=pablodieaco
GITHUB_REGISTRY=ghcr.io
FULL_IMAGE=$(GITHUB_REGISTRY)/$(GITHUB_USER)/$(IMAGE_NAME):$(IMAGE_TAG)

# Carpeta temporal del core
CORE_TEMP=_core_temp

# Ruta al core original
CORE_ORIGIN=../quant-drl-core

.PHONY: build save load push pull clean

# Copia el core, construye el contenedor, borra la copia temporal
build:
	@echo "Copiando quant-drl-core a $(CORE_TEMP)..."
	rsync -av --exclude '.git/' --exclude 'notebooks/' --exclude 'logs/' --exclude 'models/' --exclude '.venv/' --exclude '__pycache__/' $(CORE_ORIGIN)/ $(CORE_TEMP)/

	@echo "Construyendo imagen Docker..."
	docker compose build

	@echo "Limpiando copia temporal..."
	rm -rf $(CORE_TEMP)

	@echo "Build completado."

# Ejecuta el contenedor
run:
	@echo "Ejecutando contenedor..."
	docker compose up -d

	@echo "Contenedor ejecutándose."

# Guarda la imagen en un archivo .tar
save:
	@echo "Guardando imagen como $(TAR_FILE)..."
	docker save -o $(TAR_FILE) $(IMAGE_NAME)

# Carga la imagen desde un archivo .tar
load:
	@echo "Cargando imagen desde $(TAR_FILE)..."
	docker load -i $(TAR_FILE)

# Subir a GitHub Container Registry
push:
	docker tag $(IMAGE_NAME) $(FULL_IMAGE)
	docker push $(FULL_IMAGE)

# Descargar desde GitHub Container Registry
pull:
	docker pull $(FULL_IMAGE)

# Elimina la imagen local y el archivo tar
clean:
	docker rmi $(IMAGE_NAME) || true
	rm -f $(TAR_FILE)
