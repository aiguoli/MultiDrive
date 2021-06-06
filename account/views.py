from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import LoginForm, RegisterForm
from django.contrib.auth import authenticate, login, logout


def user_login(request):
    if request.method == 'POST':
        user_login_form = LoginForm(data=request.POST)
        if user_login_form.is_valid():
            data = user_login_form.cleaned_data
            user = authenticate(username=data['username'], password=data['password'])
            if user:
                login(request, user)
                return redirect("storage:index")
            else:
                return HttpResponse("账号或密码输入有误。请重新输入~")
        else:
            return HttpResponse("账号或密码输入不合法")
    elif request.method == 'GET':
        user_login_form = LoginForm()
        context = {'form': user_login_form}
        return render(request, 'account/login.html', context)
    else:
        return HttpResponse("请使用GET或POST请求数据")


def user_register(request):
    if request.method == 'POST':
        user_register_form = RegisterForm(data=request.POST)
        if user_register_form.is_valid():
            new_user = user_register_form.save(commit=False)
            # 设置密码
            new_user.set_password(user_register_form.cleaned_data['password'])
            new_user.save()
            # 保存好数据后立即登录并返回博客列表页面
            login(request, new_user)
            return redirect("storage:index")
        else:
            return HttpResponse("注册表单输入有误。请重新输入~")
    elif request.method == 'GET':
        user_register_form = RegisterForm()
        context = {'form': user_register_form }
        return render(request, 'register.html', context)
    else:
        return HttpResponse("请使用GET或POST请求数据")


def user_logout(request):
    logout(request)
    return redirect("storage:index")
