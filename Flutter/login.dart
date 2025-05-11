import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_application_3/home.dart';
import 'package:flutter_application_3/create_account.dart';
//import 'package:flutter_application_3/user_service.dart';
//import 'package:flutter_application_3/account.dart';
import 'package:flutter_application_3/forgot_password.dart';
import 'package:flutter_application_3/map.dart';

import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:http/http.dart' as http;

//มีnotification
final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
    FlutterLocalNotificationsPlugin();

Future<void> _showNotification2() async {
  AndroidNotificationDetails androidNotificationDetails =
      AndroidNotificationDetails('nextflow_noti_001', 'Urgent Alert',
          playSound: true,
          sound: RawResourceAndroidNotificationSound(
              'notification.mp3'.split('.').first),
          importance: Importance.max,
          priority: Priority.high,
          ticker: 'ticker');

  NotificationDetails platformChannelDetails = NotificationDetails(
    android: androidNotificationDetails,
  );

  await flutterLocalNotificationsPlugin.show(0, 'Emergency!',
      'Open the app to view the location.', platformChannelDetails);
}

//เมื่อปิดแอพมีการจำค่าuserกับpassword
class LoginPage extends StatefulWidget {
  const LoginPage({super.key, required this.title});

  final String title;

  @override
  State<LoginPage> createState() => _LoginState();
}

class _LoginState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _userController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  //final UserService _userService = UserService(); // Instance of UserService
  bool _obscurePassword = true; // ตัวแปรเพื่อควบคุมการแสดง/ซ่อนรหัสผ่าน
  bool _isLoading = false; // ✅ ตัวแปรโหลด
  List<Map<String, String>> userList = [];
  bool _rememberMe = false; // ตัวแปรควบคุมสถานะ "Remember Me"
  String status = ''; // ตัวแปรเช็ค Login

  @override
  void initState() {
    super.initState();
    _checkNavigation();
    _loadRememberedData(); // โหลดข้อมูลที่บันทึกไว้เมื่อเปิดแอพใหม่
  }

  //ฟังก์ชันตรวจสอบ _hasFetchedLocation
  Future<void> _checkNavigation() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    bool hasFetchedLocation = prefs.getBool('hasFetchedLocation') ?? false;

    if (hasFetchedLocation) {
      final latitude = prefs.getString('rememberlatitude') ?? '';
      final longitude = prefs.getString('rememberlongitude') ?? '';

      WidgetsBinding.instance.addPostFrameCallback((_) {
        _showNotification2();
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => MapsPage(
              latitude: latitude,
              longitude: longitude,
            ),
          ),
        );
      });
    }
  }

  // โหลดข้อมูลจาก SharedPreferences
  Future<void> _loadRememberedData() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    setState(() {
      _rememberMe = prefs.getBool('rememberMe') ?? false;
      status = prefs.getString('rememberstatus') ?? '';
      if (_rememberMe) {
        _userController.text = prefs.getString('rememberUser') ?? '';
        _passwordController.text = prefs.getString('rememberPassword') ?? '';
        if (status == 'Login')
          //ไปยังหน้า MyHomePage
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (context) => const MyHomePage(),
            ),
          );
      }
    });
  }

  // บันทึกข้อมูลเมื่อผู้ใช้เลือก Remember Me และ เก็บข้อมูลเพื่อไปโชว์หน้าAccount Page
  Future<void> _saveRememberedData(
      String user, String password, String name, String role) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    if (_rememberMe) {
      await prefs.setBool('rememberMe', true);
      //await prefs.setString('rememberUser', user);
      await prefs.setString('rememberPassword', password);
      await prefs.setString('rememberstatus', 'Login'); //Set status Login
    } else {
      //await prefs.setString('rememberUser', user);
      await prefs.setBool('rememberMe', false);
      //await prefs.remove('savedUser');
      //await prefs.remove('savedPassword');
    }
    await prefs.setString('rememberUser', user); //เก็บข้อมูล
    await prefs.setString('savedUser', name); //เก็บข้อมูล
    await prefs.setString('savedPassword', password); //เก็บข้อมูล
    await prefs.setString('savedrole', role); //เก็บข้อมูล
  }

  //โหลดข้อมูลจาก google sheet
  Future<void> fetchUsers() async {
    setState(() {
      _isLoading = true; //เริ่มการโหลด
    });

    final String url =
        'https://script.google.com/macros/s/AKfycbwqdzf3uekN9H025xXyzCgnwYeMSkKcfulvK2l5C0NirpQVn9G5r30DlP-iKOWkjjyw/exec';

    try {
      final response = await http.get(Uri.parse(url));

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        userList = data.map<Map<String, String>>((user) {
          return {
            'name': user['name'].toString(),
            'username': user['username'].toString(),
            'password': user['password'].toString(),
            'role': user['role'].toString(),
            'status': user['status'].toString(),
          };
        }).toList();
      } else {
        print("❌ Failed to fetch data. Code: ${response.statusCode}");
      }
    } catch (e) {
      print("⚠️ Error: $e");
    }

    /*
    setState(() {
      _isLoading = false; //เสร็จสิ้นการโหลด
    });*/
  }

  Future<void> SetLogin(String username) async {
    final url = Uri.parse(
      'https://script.google.com/macros/s/AKfycbwqdzf3uekN9H025xXyzCgnwYeMSkKcfulvK2l5C0NirpQVn9G5r30DlP-iKOWkjjyw/exec',
    );

    await http.post(url, body: {
      'action': 'Login',
      'username': username,
    });

    setState(() {
      _isLoading = false; //เสร็จสิ้นการโหลด
    });

    /*if (response.statusCode == 200) {
      final result = jsonDecode(response.body);
      print("✅ ${result['message']}");
    } else {
      print("❌ Failed to delete user");
    }*/
  }

  //Check Login to Homepage
  Future<void> checkLogin() async {
    //SharedPreferences prefs = await SharedPreferences.getInstance();

    if (!_formKey.currentState!.validate()) return;

    await fetchUsers();

    final inputUsername = _userController.text;
    final inputPassword = _passwordController.text;
    Map<String, String>? match;

    for (var user in userList) {
      if (user['username'] == inputUsername &&
          user['password'] == inputPassword &&
          user['status'] == 'Logout') {
        match = user;
        break;
      }
    }

    if (match != null) {
      // Save ข้อมูล
      await _saveRememberedData(
        inputUsername,
        inputPassword,
        match['name']!,
        match['role']!,
      );

      //Set Login Status
      /*await prefs.setString('rememberstatus', 'Login');*/
      await SetLogin(inputUsername);

      /*
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: Text("✅ Login Success"),
          content: Text("Welcome, ${match?['name']}!"),
        ),
      );
      */

      // 👉 ส่ง user ไปยังหน้า MyHomePage โดยไม่ต้องเปิด dialog
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => const MyHomePage(),
        ),
      );

      /*AccountPage(
        user: match['name']!,
      ); //ส่งค่าไปหน้าAccountPage*/
    } else {
      setState(() {
        _isLoading = false; //เสร็จสิ้นการโหลด
      });
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: Text("❌ Login Failed"),
          content: Text("Username or Password is incorrect."),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
      ),
      body: SafeArea(
        child: _isLoading
            ? Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(),
                    SizedBox(height: 12),
                    Text("Processing....."),
                  ],
                ),
              )
            : SingleChildScrollView(
                padding: const EdgeInsets.all(16.0),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      TextFormField(
                        controller: _userController,
                        decoration: InputDecoration(labelText: 'Username'),
                        validator: (input) {
                          if (input == null || input.isEmpty) {
                            return 'Please Enter Username';
                          }
                          return null;
                        },
                      ),
                      TextFormField(
                        controller: _passwordController,
                        decoration: InputDecoration(
                          labelText: 'Password',
                          suffixIcon: IconButton(
                            icon: Icon(
                              _obscurePassword
                                  ? Icons.visibility
                                  : Icons.visibility_off,
                            ),
                            onPressed: () {
                              setState(() {
                                _obscurePassword = !_obscurePassword;
                              });
                            },
                          ),
                        ),
                        obscureText: _obscurePassword,
                        validator: (input) {
                          if (input == null || input.isEmpty) {
                            return 'Please Enter Password';
                          }
                          return null;
                        },
                      ),
                      SizedBox(height: 10),
                      Row(
                        children: <Widget>[
                          Checkbox(
                            value: _rememberMe,
                            onChanged: (bool? value) {
                              setState(() {
                                _rememberMe = value ?? false;
                              });
                            },
                          ),
                          const Text('Remember Me'),
                        ],
                      ),
                      SizedBox(height: 10),
                      FloatingActionButton.extended(
                        onPressed: checkLogin,
                        label: Text("Login"),
                        icon: Icon(Icons.login),
                      ),
                      SizedBox(height: 10),
                      OutlinedButton(
                        onPressed: () {
                          showDialog(
                            context: context,
                            builder: (BuildContext context) {
                              return AlertDialog(
                                title: Text('Are you sure?'),
                                content:
                                    Text('All entered data will be deleted.'),
                                actions: <Widget>[
                                  TextButton(
                                    onPressed: () {
                                      _formKey.currentState!.reset();
                                      setState(() {
                                        _userController.clear();
                                        _passwordController.clear();
                                      });
                                      Navigator.of(context).pop();
                                    },
                                    child: Text('Clear'),
                                  ),
                                  TextButton(
                                    onPressed: () {
                                      Navigator.of(context).pop();
                                    },
                                    child: Text('Cancel'),
                                  ),
                                ],
                              );
                            },
                          );
                        },
                        child: Text('Clear'),
                      ),
                      SizedBox(height: 10),
                      GestureDetector(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                                builder: (context) => const CreateAccountPage(
                                    title: 'Create Account')),
                          );
                        },
                        child: Text(
                          'Create an account',
                          style: TextStyle(
                            color: Colors.blue,
                            decoration: TextDecoration.underline,
                          ),
                        ),
                      ),
                      SizedBox(height: 10),
                      GestureDetector(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => ForgotPasswordPage(
                                user: _userController.text,
                              ),
                            ),
                          );
                        },
                        child: Text(
                          'Forgot Password??',
                          style: TextStyle(
                            color: Colors.red,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
      ),
    );
  }
}



/*class LoginPage extends StatefulWidget {
  const LoginPage({super.key, required this.title});

  final String title;

  @override
  State<LoginPage> createState() => _LoginState();
}

class _LoginState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
      ),
      body: Container(
        padding: EdgeInsets.all(10),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              SizedBox(
                height: 15,
              ),
              Text('user:'),
              TextFormField(
                validator: (input) {
                  if (input == null || input.isEmpty) {
                    return "Please Enter user";
                  }

                  return null;
                },
              ),
              SizedBox(
                height: 15,
              ),
              Text('Password:'),
              TextFormField(
                validator: (input) {
                  if (input == null || input.isEmpty) {
                    return "Please Enter Password";
                  }

                  return null;
                },
              ),
              SizedBox(
                height: 15,
              ),
              Row(
                children: <Widget>[
                  Expanded(
                    child: FloatingActionButton(
                      onPressed: () {
                        bool pass = _formKey.currentState!.validate();
                        if (pass) {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                                builder: (context) =>
                                    const MyHomePage(title: 'Home Page')),
                          );
                        }
                      },
                      child: const Text('Login'),
                    ),
                  ),
                ],
              ),
              Row(
                children: <Widget>[
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () {
                        showDialog(
                          context: context,
                          builder: (BuildContext context) {
                            return AlertDialog(
                              title: Text('Are you sure?'),
                              content: Text('All entered data will be deleted.'),
                              actions: <Widget>[
                                TextButton(
                                  onPressed: () {
                                    _formKey.currentState!
                                        .reset(); // Clears the form after dialog is shown
                                    Navigator.of(context)
                                        .pop(); // Closes the dialog
                                  },
                                  child: Text('Clear'),
                                ),
                                TextButton(
                                  onPressed: () {
                                    Navigator.of(context)
                                        .pop(); // Closes the dialog
                                  },
                                  child: Text('Cancel'),
                                ),
                              ],
                            );
                          },
                        );
                      },
                      child: Text('Clear Data'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
*/