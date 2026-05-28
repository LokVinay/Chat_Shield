from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import Http404
from .models import *
from .forms import ChatmessageCreateForm
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@login_required
def chat_view(request, chatroom_name= 'public-chat'):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    chat_messages = chat_group.chat_messages.all()[:30]
    form = ChatmessageCreateForm()

    other_user = None
    if chat_group.is_private:
        if request.user not in chat_group.members.all():
            raise Http404()
        for member in chat_group.members.all():
            other_user= member
            break

    if request.htmx:
        form = ChatmessageCreateForm(request.POST)
        if form.is_valid:
            message = form.save(commit=False)
            message.author = request.user
            message.group = chat_group
            message.save()
            context = {
                'message' : message,
                'user' : request.user
            }
            return render(request, 'realtime_chatter/partials/chat_message_p.html', context)
        
    context = {
        'chat_messages' : chat_messages,
        'form' : form,
        'other_user' : other_user,
        'chatroom_name' : chatroom_name
    }

    return render(request, 'realtime_chatter/chat.html', context)

@login_required
def get_or_create_chatroom(request, username):
    if request.user.username == username:
        return redirect('home')
    
    other_user = User.objects.get(username= username)
    my_chatrooms = request.user.chat_groups.filter(is_private= True)

    if my_chatrooms.exists():
        for chatroom in my_chatrooms:
            if other_user in chatroom.members.all():
                chatroom= chatroom
                break

            else:
                chatroom= ChatGroup.objects.create(is_private= True)
                chatroom.members.add(other_user, request.user)
    
    else:
        chatroom= ChatGroup.objects.create(is_private= True)
        chatroom.members.add(other_user, request.user)

    return redirect('chatroom', chatroom.group_name)


from django.http import JsonResponse

import json
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def start_extraction(request, room_id):

    if request.method == "POST":

        try:

            data = json.loads(request.body)

            messages = data.get("messages", [])

            print("📩 Received Messages:")
            print(messages)

            # 🔥 THREAT KEYWORDS
            threat_keywords = [
                "otp",
                "password",
                "bank",
                "credit card",
                "cvv",
                "send money",
                "click this link",
                "verify account",
                "upi",
                "urgent",
                "login",
                "pin",
                "hack",
                "telegram",
                "lottery",
                "prize"
            ]

            threat_score = 0

            # 🔍 CHECK EACH MESSAGE
            for msg in messages:

                lower_msg = msg.lower()

                print("🔎 Checking:", lower_msg)

                for keyword in threat_keywords:

                    if keyword in lower_msg:

                        print("⚠ Threat Keyword Found:", keyword)

                        threat_score += 20

            # 🎯 LIMIT SCORE
            if threat_score > 100:
                threat_score = 100

            # 🎯 VERDICT
            if threat_score > 70:
                verdict = "POTENTIAL THREAT"

            elif threat_score > 40:
                verdict = "MEDIUM RISK"

            else:
                verdict = "SAFE"

            return JsonResponse({
                "confidence": threat_score,
                "verdict": verdict
            })

        except Exception as e:

            print("❌ ERROR:", str(e))

            return JsonResponse({
                "confidence": 0,
                "verdict": "ERROR"
            })

    return JsonResponse({
        "confidence": 0,
        "verdict": "INVALID REQUEST"
    })

@csrf_exempt
def stop_extraction(request):
    return JsonResponse({
        "message": "Stopped Successfully"
    })