# Nombre de la imagen
IMAGE_NAME=quant-drl-web
IMAGE_TAG=latest
TAR_FILE=$(IMAGE_NAME).tar

# GitHub Container Registry
GITHUB_USER=pablodieaco
GITHUB_REGISTRY=ghcr.io
FULL_IMAGE=$(GITHUB_REGISTRY)/$(GITHUB_USER)/$(IMAGE_NAME):$(IMAGE_TAG)


.PHONY: build save load push pull clean

# Copia el core, construye el contenedor, borra la copia temporal
build:
	@echo "Construyendo imagen Docker..."
	docker compose --profile local build

	@echo "Build completado."

# Ejecuta el contenedor
run:
	@echo "Ejecutando contenedor..."
	docker compose --profile remote up -d

	@echo "Contenedor ejecutándose."

# Ejecuta el contenedor usando la imagen local
run-local:
	@echo "Ejecutando contenedor..."
	docker compose --profile local up

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
