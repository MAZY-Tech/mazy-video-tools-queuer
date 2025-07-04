ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text)
AWS_REGION ?= $(shell aws configure get region)
SAM_STACK_NAME ?= mazy-video-tools-queuer

.PHONY: build start invoke logs clean

login:
	aws ecr get-login-password --region $(AWS_REGION) \
	  | docker login --username AWS --password-stdin $(ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

build:
	sam build

deploy: build
	sam deploy

clean:
	rm -rf .aws-sam
