#!/usr/bin/python
#
# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# from google.cloud import vision

import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.views.decorators.http import require_http_methods
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from store.models import Product, SiteConfig, Testimonial, Transaction
from store.serializers import (
    ProductSerializer,
    SiteConfigSerializer,
    TestimonialSerializer,
    CartSerializer,
    CheckoutSerializer,
)

# newly added code
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from store.models import Video
from store.serializers import VideoSerializer

class VideoUploadViewSet(viewsets.ModelViewSet):
    # queryset = Product.objects.all()
    serializer_class = VideoSerializer
    parser_classes = (MultiPartParser, FormParser)

    #def uploadvideo(self, request, *args, **kwargs):
    @action(detail=True, methods=["get", "post"])
    def uploadvideo(self, request):
        print("in uploadvideo")
        file_serializer = VideoSerializer(data=request.data)
        print(file_serializer)
        if file_serializer.is_valid():
            file_serializer.save()
            return Response({
                "message": "Upload successful!",
                "video_url": file_serializer.data["video"]
            }, status=status.HTTP_201_CREATED)
        return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
##################################

class ProductPurchaseException(APIException):
    status_code = 405
    default_detail = {
        "code": status_code,
        "message": "Unable to complete purchase - no inventory",
    }

def testMethod():
    print("test method")

def log_error(error_name, error_message, product):
    # Log error by writing structured JSON. Can be then used with log-based alerting, metrics, etc.
    print(
        json.dumps(
            {
                "severity": "ERROR",
                "error": error_name,
                "message": f"{error_name}: {error_message}",
                "method": "ProductViewSet.purchase()",
                "product": product.id,
                "countRequested": 1,
                "countFulfilled": product.inventory_count,
            }
        )
    )

class UploadViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    parser_classes = (MultiPartParser, FormParser)

    # To work on this method to handle video upload .....
    # @ensure_csrf_cookie
    # @require_http_methods(["POST"])
    # def upload(request):   
    @action(detail=True, methods=["get", "post"])
    def upload(self, request, pk):
        print("in upload")

        product = get_object_or_404(Product, id=pk)
        data = VideoSerializer(data=request.data)
        # data=json.loads(request.body)
        print(f"printing request: {request}" )
        print(data)
        
        # product.video = data["video"]


        # def lift_item_status(data):
        #     status = ""
        #     for item in data["items"]:
        #         if "status" in item:
        #             for i in item["status"]:
        #                 status = str(i)
        #     return status

        # serializer = CartSerializer(data=json.loads(request.body))

        # if not serializer.is_valid():
        #     status_code = 400
        #     status = "validation_error"
        #     if "payment" in serializer.errors:
        #         status_code = 501
        #         status = serializer.errors["payment"]["method"][0].code
        #     if "items" in serializer.errors:
        #         status = lift_item_status(serializer.errors)
        #     return JsonResponse(
        #         {"status": status, "errors": serializer.errors}, status=status_code
        #     )

        # cart = serializer.validated_data

        # items = []
        # for item in cart["items"]:
        #     product = get_object_or_404(Product, id=item["id"])
        #     count = item["countRequested"]

        #     product.inventory_count -= count
        #     product.save()
        #     for _ in range(count):
        #         Transaction.objects.create(
        #             datetime=timezone.now(), product_id=product, unit_price=product.price
        #         )
        #     items.append(
        #         {"id": product.id, "countRequested": count, "countFulfilled": count}
        #     )

        #     if product.inventory_count == 0:
        #         log_error(
        #             "INVENTORY_SOLDOUT_ERROR",
        #             "A purchase just caused a product to sell out. More inventory will be required.",
        #             product,
        #         )

        # response = CheckoutSerializer(data={"status": "complete", "items": items})
        # response.is_valid()
        # return JsonResponse(response.data)   

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    parser_classes = (MultiPartParser, FormParser)

    class ProductPurchaseException(APIException):
        status_code = 405
        default_detail = {
            "code": status_code,
            "message": "Unable to complete purchase - no inventory",
        }

    # def detect_labels_uri(uri):
    #     """Detects labels in the file located in Google Cloud Storage or on the
    #     Web."""
    #     client = vision.ImageAnnotatorClient()
    #     image = vision.Image()
    #     image.source.image_uri = uri

    #     response = client.label_detection(image=image)
    #     labels = response.label_annotations
    #     print("Labels:")

    #     for label in labels:
    #         print(label.description)

    #     if response.error.message:
    #         raise Exception(
    #             "{}\nFor more info on error messages, check: "
    #             "https://cloud.google.com/apis/design/errors".format(response.error.message)
    #         )

    @action(detail=True, methods=["get", "post"])
    def purchase(self, request, pk):
        test = False
        product = get_object_or_404(Product, id=pk)
        print(f"printing request: {request}" )

        # data = VideoSerializer(data=request.data)
        product.video = request.data["video"]
        print(f"printing request.data: {request.data}" )

       
        # product.video = data["video"]
        product.save()
        print(product.video.url)
        path = product.video.url
        product.analysis2(path)

        # print(product.video.title)

        # file_serializer = VideoSerializer(data=request.data)
        # print(file_serializer)

        # video_url = file_serializer.data["video"]
        # print(video_url)


        # if file_serializer.is_valid():
        #     file_serializer.save()
        #     return Response({
        #         "message": "Upload successful!",
        #         "video_url": file_serializer.data["video"]
        #     }, status=status.HTTP_201_CREATED)
        # return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # data = VideoSerializer(data=request.data)
        # # data=json.loads(request.body)
        # print(f"printing request: {request}" )
        # print(data)
        
        # product.video = data["video"]
        # product.save()

        # print(product.video.path)

        # product.analysis2(data)

        # # detect_labels_uri(product.image)
        # video_uri = "gs://media-bd80-448911-64ca/test_frames/happybirthday.mp4"
        # # video_uri = "gs://media-bd80-448911-64ca/test_frames/swear.mp4"
        # img_uri = ""
        # #testMethod()
        # #product.detect_labels()
        # #product.detect_safe_search(img_uri)
        # #product.sync_recognize_with_profanity_filter_gcs(video_uri)
        
        # if not test:
        #     product.analysis()
        # else:
        #     print("purchase")

        # if product.inventory_count > 0:
        #     product.inventory_count += 1
        #     product.save()
        #     Transaction.objects.create(
        #         datetime=timezone.now(), product_id=product, unit_price=product.price
        #     )
        # else:
        #     log_error(
        #         "INVENTORY_COUNT_ERROR",
        #         "A purchase was attempted where there was insufficient inventory to fulfil the order.",
        #         product,
        #     )
        #     raise ProductPurchaseException()

        # # If the transaction caused a product to sell out, log an error
        # if product.inventory_count == 0:
        #     log_error(
        #         "INVENTORY_SOLDOUT_ERROR",
        #         "A purchase just caused a product to sell out. More inventory will be required.",
        #         product,
        #     )

        serializer = ProductSerializer(product)
        return Response(serializer.data)


class ActiveProductViewSet(viewsets.ViewSet):
    @extend_schema(request=None, responses=ProductSerializer)
    def list(self, request, formatting=None):
        active_product = get_object_or_404(Product, active=True)
        serializer = ProductSerializer(active_product, context={"request": request})
        return Response(serializer.data)


class TestimonialViewSet(viewsets.ModelViewSet):
    queryset = Testimonial.objects.order_by("-rating").all()
    serializer_class = TestimonialSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["product_id"]


class SiteConfigViewSet(viewsets.ModelViewSet):
    queryset = SiteConfig.objects.all()
    serializer_class = SiteConfigSerializer


class ActiveSiteConfigViewSet(viewsets.ViewSet):
    @extend_schema(responses=SiteConfigSerializer)
    def list(self, request, formatting=None):
        active = get_object_or_404(SiteConfig, active=True)
        serializer = SiteConfigSerializer(active)
        return Response(serializer.data)


 # queryset = Product.objects.all()
    

@ensure_csrf_cookie
@require_http_methods(["POST"])
def videoupload(self, request):
    serializer_class = VideoSerializer
    parser_classes = (MultiPartParser, FormParser)
    print("in videoupload")
    file_serializer = VideoSerializer(data=request.data)
    print(file_serializer)
    if file_serializer.is_valid():
        file_serializer.save()
        return Response({
            "message": "Upload successful!",
            "video_url": file_serializer.data["video"]
        }, status=status.HTTP_201_CREATED)
    return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@ensure_csrf_cookie
@require_http_methods(["POST"])
def checkout(request):
    def lift_item_status(data):
        status = ""
        for item in data["items"]:
            if "status" in item:
                for i in item["status"]:
                    status = str(i)

        return status

    serializer = CartSerializer(data=json.loads(request.body))

    if not serializer.is_valid():
        status_code = 400
        status = "validation_error"
        if "payment" in serializer.errors:
            status_code = 501
            status = serializer.errors["payment"]["method"][0].code
        if "items" in serializer.errors:
            status = lift_item_status(serializer.errors)
        return JsonResponse(
            {"status": status, "errors": serializer.errors}, status=status_code
        )

    cart = serializer.validated_data

    items = []
    for item in cart["items"]:
        product = get_object_or_404(Product, id=item["id"])
        count = item["countRequested"]

        product.inventory_count -= count
        product.save()
        for _ in range(count):
            Transaction.objects.create(
                datetime=timezone.now(), product_id=product, unit_price=product.price
            )
        items.append(
            {"id": product.id, "countRequested": count, "countFulfilled": count}
        )

        if product.inventory_count == 0:
            log_error(
                "INVENTORY_SOLDOUT_ERROR",
                "A purchase just caused a product to sell out. More inventory will be required.",
                product,
            )

    response = CheckoutSerializer(data={"status": "complete", "items": items})
    response.is_valid()
    return JsonResponse(response.data)


def csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})
