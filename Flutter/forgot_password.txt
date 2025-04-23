import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
//import 'package:flutter_application_3/user_service.dart';

class ForgotPasswordPage extends StatefulWidget {
  final String? user;

  const ForgotPasswordPage({Key? key, this.user}) : super(key: key);

  @override
  State<ForgotPasswordPage> createState() => _ForgotPasswordState();
}

class _ForgotPasswordState extends State<ForgotPasswordPage> {
  String? user;
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _userController = TextEditingController();

  List<Map<String, String>> userList = [];
  bool _isLoading = false; // ✅ ตัวแปรโหลด

  @override
  void initState() {
    super.initState();
    _userController.text = widget.user!;
  }

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

  Future<void> getpassword() async {
    if (!_formKey.currentState!.validate()) return;

    await fetchUsers();

    final inputUsername = _userController.text;
    //final inputPassword = _passwordController.text;
    Map<String, String>? match;

    for (var user in userList) {
      if (user['username'] == inputUsername) {
        match = user;
        break;
      }
    }

    if (match != null) {
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: Text("✅ Password Found"),
          content: Text("Password for $inputUsername: ${match?['password']}!"),
        ),
      );
    } else {
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: Text("❌ Password Not Found"),
          content: Text("Please try again....."),
        ),
      );
    }
  }

  /*Future<void> _CheckData(String username) async {
    // ดึงข้อมูลผู้ใช้ทั้งหมด
    List<Map<String, String>> userDetails =
        await _userService.getAllUserDetails();

    // ค้นหา username ที่ตรงกัน
    for (var user in userDetails) {
      if (username == user['username']) {
        // พบ username ที่ตรงกัน แสดง password
        String? password = user['password'];
        showDialog(
          context: context,
          builder: (context) {
            return AlertDialog(
              title: Text('Password Found'),
              content: Text('Password for $username: $password'),
              actions: [
                TextButton(
                  onPressed: () {
                    Navigator.of(context).pop(); // ปิด Dialog
                  },
                  child: Text('OK'),
                ),
              ],
            );
          },
        );
        return; // จบการทำงานเมื่อพบ username
      }
    }

    // ไม่พบ username
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Username not found!')),
    );
  }*/

  @override
  Widget build(BuildContext context) {
    return Scaffold(
        appBar: AppBar(
          backgroundColor: Theme.of(context).colorScheme.tertiary,
          title: const Text('Forgot Password'),
        ),
        body: Padding(
          padding: const EdgeInsets.all(10),
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
              : Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
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
                      //Get Password
                      Row(
                        children: <Widget>[
                          Expanded(
                            child: FloatingActionButton(
                              onPressed: getpassword,
                              backgroundColor: Colors.red[300],
                              child: const Text('Get Password'),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
        ));
  }
}
