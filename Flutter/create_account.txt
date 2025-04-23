import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_application_3/login.dart';
import 'package:http/http.dart' as http;
//import 'package:flutter_application_3/user_service.dart';

Future<void> sendDataToGoogleSheet({
  required String name,
  required String username,
  required String password,
  //required String role,
}) async {
  //ใส่ URL ของ Google Apps Script ที่ deploy แล้ว
  final String url =
      'https://script.google.com/macros/s/AKfycbwqdzf3uekN9H025xXyzCgnwYeMSkKcfulvK2l5C0NirpQVn9G5r30DlP-iKOWkjjyw/exec';
  /*'https://script.google.com/macros/s/AKfycbzjvaqLsOJ6bYnMM4rHXRYgNb1iXkjr7ApNrhx8Jw1fsC7kTsFl8xuPpFSeHgo1NXL-/exec';*/

  try {
    /*await http.post(
      Uri.parse(url),
      body: {
        'action': 'register',
        'name': name,
        'username': username,
        'password': password,
        //'role': role,
      },
    );*/

    await http.post(
      Uri.parse(url),
      body: {
        'action': 'register',
        'name': name,
        'username': username,
        'password': password,
        //'role': role,
      },
    );

    /*final response = await http.post(
      Uri.parse(url),
      body: {
        'name': name,
        'username': username,
        'password': password,
        //'role': role,
      },
    );*/
    /*
    if (response.statusCode == 200) {
      print(
          "✅ Data sent successfully: ${response.body}"); //ใช้ http get จะเข้าอันนี้
    } else {
      print(
          "❌ Failed to send data. Status code: ${response.statusCode}"); //เข้าอันนี้เป็นการredirect
    }*/
  } catch (e) {
    print("⚠️ Error occurred: $e");
  }
}

class CreateAccountPage extends StatefulWidget {
  const CreateAccountPage({super.key, required this.title});

  final String title;

  @override
  State<CreateAccountPage> createState() => _CreateAccountState();
}

class _CreateAccountState extends State<CreateAccountPage> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _nameController =
      TextEditingController(); //name input
  final TextEditingController _userController =
      TextEditingController(); //username input
  final TextEditingController _passwordController =
      TextEditingController(); //password input
  bool _obscurePassword = true; // ตัวแปรเพื่อควบคุมการแสดง/ซ่อนรหัสผ่าน

  bool _isLoading = false;
  List<Map<String, String>> userList = [];

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
            //'password': user['password'].toString(),
            //'role': user['role'].toString(),
          };
        }).toList();
      } else {
        print("❌ Failed to fetch data. Code: ${response.statusCode}");
      }
    } catch (e) {
      print("⚠️ Error: $e");
    }

    setState(() {
      _isLoading = false; //เสร็จสิ้นการโหลด
    });
  }

  //Check Login to Homepage
  Future<void> checkcreate() async {
    if (!_formKey.currentState!.validate()) return;

    await fetchUsers();

    final inputName = _nameController.text;
    final inputUsername = _userController.text;
    Map<String, String>? match;

    for (var user in userList) {
      if (user['name'] == inputName || user['username'] == inputUsername) {
        match = user;
        break;
      }
    }

    if (match != null) {
      //เมื่อมีnameหรือusernameแล้วในระบบ
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: Text("❌ Create Account Failed"),
          content: Text("Name or Username is already in the system."),
        ),
      );
    } else {
      sendDataToGoogleSheet(
        name: _nameController.text,
        username: _userController.text,
        password: _passwordController.text,
      );

      // 👉 ส่ง user ไปยังหน้า LoginPage โดยไม่ต้องเปิด dialog
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => const LoginPage(title: 'Login'),
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
                      children: <Widget>[
                        SizedBox(
                          height: 10,
                        ),
                        TextFormField(
                          controller: _nameController,
                          decoration: InputDecoration(labelText: 'Name'),
                          validator: (input) {
                            if (input == null || input.isEmpty) {
                              return 'Please Enter Name';
                            }
                            return null;
                          },
                        ),
                        SizedBox(
                          height: 10,
                        ),
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
                        SizedBox(
                          height: 10,
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
                          obscureText:
                              _obscurePassword, // ควบคุมการแสดง/ซ่อนรหัสผ่าน
                          validator: (input) {
                            if (input == null || input.isEmpty) {
                              return 'Please Enter Password';
                            }
                            return null;
                          },
                        ),
                        SizedBox(
                          height: 10,
                        ),

                        //Create data
                        FloatingActionButton.extended(
                          onPressed: checkcreate,
                          label: Text("Create"),
                          backgroundColor: Colors.blue[300],
                        ),

                        //Clear data
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
                                          _nameController.clear();
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

                        /* //Create data
                        Row(
                          children: <Widget>[
                            Expanded(
                              child: FloatingActionButton(
                                onPressed: () async {
                                  bool pass = _formKey.currentState!.validate();
                                  if (pass) {
                                    /*await _userService.saveUser(
                              _userController.text,
                              _passwordController.text,
                            );*/
                                    sendDataToGoogleSheet(
                                      name: _nameController.text,
                                      username: _userController.text,
                                      password: _passwordController.text,
                                    );

                                    Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (context) =>
                                            const LoginPage(title: 'Login'),
                                      ),
                                    ); //ไปหน้าLoginเพื่อยืนยันตัวตน

                                    /*Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (context) =>
                                    const MyHomePage(title: 'Fall Detection'),
                              ),
                            ); //ไปหน้าHome*/
                                  }
                                },
                                backgroundColor: Colors.blue[300],
                                child: const Text('Create'),
                              ),
                            ),
                          ],
                        ),*/

                        /* //Clear data
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
                                        content: Text(
                                            'All entered data will be deleted.'),
                                        actions: <Widget>[
                                          TextButton(
                                            onPressed: () {
                                              _formKey.currentState!.reset();
                                              setState(() {
                                                _nameController.clear();
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
                            ),
                          ],
                        ),*/
                        /*SizedBox(
                          height: 10,
                        ),*/
                        /*  //Delete All Account
                Row(
                  children: <Widget>[
                    GestureDetector(
                      onTap: () {
                        showDialog(
                          context: context,
                          builder: (BuildContext context) {
                            return AlertDialog(
                              title: Text('Are you sure?'),
                              content: Text('All data will be deleted.'),
                              actions: <Widget>[
                                TextButton(
                                  onPressed: () async {
                                    await _userService.clearAllUsers();
                                    /*// ล้างข้อมูลใน SharedPreferences คือการลบข้อมูลทั้งหมด
                                    SharedPreferences prefs =
                                        await SharedPreferences.getInstance();
                                    await prefs.remove('user');
                                    await prefs.remove('password');*/
                                    setState(() {
                                      _userController.clear();
                                      _passwordController.clear();
                                    });
                                    Navigator.of(context).pop();
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(
                                          content:
                                              Text('All accounts deleted.')),
                                    );
                                    Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (context) => LoginPage(
                                          title: 'Login',
                                        ),
                                      ),
                                    );
                                  },
                                  child: Text('Delete'),
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
                      child: Text(
                        'Delete all account',
                        style: TextStyle(
                          color: Colors.red,
                        ),
                      ),
                    ),
                  ],
                ), */
                      ],
                    ),
                  ),
                )),
    );
  }
}
