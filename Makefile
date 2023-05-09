PROJECT_ID=server
APP?=headless-invoicing
TAG?=s1.0.0

create-tf-backend-bucket:
	gsutil mb -p $(PROJECT_ID) gs://$(PROJECT_ID)-terraform

###

# check the the environment a target should be run against. If undefined, raise an error
check-env:
ifndef ENV
	$(error Please set ENV=[staging|production])
endif

# This cannot be indented or else make will include spaces in front of secret
define get-secret
$(shell gcloud secrets versions access latest --secret=$(1) --project=$(PROJECT_ID))
endef

###

terraform-create-workspace: check-env
	cd terraform && \
		terraform workspace new $(ENV)

terraform-init: check-env
	cd terraform && \
		terraform workspace select $(ENV) && \
		terraform init
GITHUB_SHA?=latest
LOCAL_TAG=$(APP):$(TAG)
REMOTE_TAG=gcr.io/$(PROJECT_ID)/$(LOCAL_TAG)
AWS_REMOTE_TAG=$(ECR_REGISTRY)/$(LOCAL_TAG)
DELETE_DEPLOYMENT?=false
IMAGE_SET?=$(REMOTE_TAG)
CONFIG_BRANCH?=staging
DEPLOY_BRANCH?=aws-staging

ifdef ECR_REGISTRY
	IMAGE_SET=$(AWS_REMOTE_TAG)
	CONFIG_BRANCH=aws-staging
	DEPLOY_BRANCH=aws-staging
endif

ifeq ($(ENV), production)
	CONFIG_BRANCH=master
	DEPLOY_BRANCH=production
	ifdef ECR_REGISTRY
		CONFIG_BRANCH=aws-master
		DEPLOY_BRANCH=aws-production
	endif
endif

test: check-env
	@echo $(CONFIG_BRANCH)

ssh: check-env
	gcloud compute ssh $(SSH_STRING) \
		--project=$(PROJECT_ID) \
		--zone=$(ZONE)

ssh-cmd: check-env
	@gcloud compute ssh $(SSH_STRING) \
		--project=$(PROJECT_ID) \
		--zone=$(ZONE) \
		--command="$(CMD)"

build: check-env
	@echo $(IMAGE_SET)
	@echo $(ENV)
	@echo $(DEPLOY_BRANCH)
	@echo $(ECR_REGISTRY)
	docker build -t $(LOCAL_TAG) .

push:
	docker tag $(LOCAL_TAG) $(REMOTE_TAG)
	docker push $(REMOTE_TAG)

aws-push: check-env
	@echo $(IMAGE_SET)
	@echo $(ENV)
	@echo $(DEPLOY_BRANCH)
	@echo $(ECR_REGISTRY)
#
	docker tag $(LOCAL_TAG) $(AWS_REMOTE_TAG)
	docker push $(AWS_REMOTE_TAG)

# the deploy make target
