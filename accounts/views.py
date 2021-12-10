from django.shortcuts import render,redirect
from .forms import RegistrationForm
from .models import Account
from django.contrib import messages,auth
from django.contrib.auth.decorators import login_required

#verification Email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.http import HttpResponse
from carts.views import _cart_id
from carts.models import Cart,CartItem
import requests

# Create your views here.
def register(request):
    if request.method =='POST':
        #post contain all field value
        form = RegistrationForm(request.POST)
        #create user
        if form.is_valid():
            #cleaned_data get data from request
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]

            user = Account.objects.create_user(first_name = first_name, last_name = last_name, email = email, username = username,password = password)
            user.phone_number = phone_number
            user.save()

            #user activation
            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user':user, #user object
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)), #encode user id
                'token':default_token_generator.make_token(user),#create token for user

            })
            #send email to .//
            to_email = email
            send_email = EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()

            #messages.success(request,'Thank you for registering with us. We have sent you a verification email to your email address.Please verify it.')
            return redirect('/accounts/login/?command=verification&email='+email)

    else:
        form = RegistrationForm()


    context = {
        'form':form,
    }

    return render(request,'accounts/register.html',context)

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email = email, password = password)

        if user is not None:
            try:
                #check is there cart item
                cart = Cart.objects.get(cart_id = _cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart = cart).exists()

                if is_cart_item_exists:
                    #get all cart items for this cartid
                    cart_item = CartItem.objects.filter(cart=cart)

                    product_variation = []
                    for item in cart_item:
                        #get all item variations
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    #get cart items from user to access variations
                    cart_item = CartItem.objects.filter(user = user)
                    ex_var_list = []
                    id = []

                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    """produuct_variation = [1,2,3,4,6]
                    ex_var_list = [4,6,3,5]


"""                 #get common variations
                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()

                        else:
                            #assign user
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user=user
                                item.save()
            except:
                pass
            auth.login(request,user)
            messages.success(request,'You are now logged in.')
            #get checkout sign in url ?next=/cart/checkout
            url = request.META.get('HTTP_REFERER')
            try:
                #query = next=/cart/checkout
                query = requests.utils.urlparse(url).query
                #key is next,value is /cart/checkout
                params = dict(x.split('=') for x in query.split('&'))

                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)

            except:
                return redirect('dashboard')

        else:
            messages.error(request,'Invalid login credentials')
            return redirect('login')

    return render(request,'accounts/login.html')

@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    messages.success(request,"You are logged out.")
    return redirect('login')

def activate(request,uidb64,token):
    try:
        #get user pk
        uid = urlsafe_base64_decode(uidb64).decode()
        #return user object
        user = Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user,token):
        user.is_active = True
        user.save()
        messages.success(request,'Congratulations! Your account is activated.')
        return redirect('login')

    else:
        messages.error(request,'Invalid activation link')
        return redirect('register')

#can access only when you login
@login_required(login_url = 'login')
def dashboard(request):
    return render(request,'accounts/dashboard.html')


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email = email).exists():
            #exact same as database,case sense
            user = Account.objects.get(email__exact = email)

            #Send reset email to user
            current_site = get_current_site(request)
            mail_subject = 'Reset your account'
            message = render_to_string('accounts/reset_password_email.html', {
                'user':user, #user object
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)), #encode user id
                'token':default_token_generator.make_token(user),#create token for user

            })
            #send email to .//
            to_email = email
            send_email = EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()

            messages.success(request,'Password reset email has been sent to your email address.')
            return redirect('login')

        else:
            messages.error(request,"Account does not exist!")
            return redirect('forgotPassword')

    return render(request,'accounts/forgotPassword.html')


def resetpassword_validate(request,uidb64,token):
    try:
        #get user pk
        uid = urlsafe_base64_decode(uidb64).decode()
        #return user object
        user = Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user,token):
            #store uid to reset password
        request.session['uid'] = uid
        messages.success(request,'Plesase reset your password')
        return redirect('resetPassword')
    else:
        messages.error(request,'This link has been expired!')
        return redirect('login')

def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk = uid)
            #hash the password and change to the database
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect('login')

        else:
            messages.error(request,'Password do not match!')
            return redirect('resetPassword')
    else:
        return render(request,'accounts/resetPassword.html')
