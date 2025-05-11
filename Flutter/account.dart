import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

class AccountPage extends StatefulWidget {
  final String user;
  final String role;

  const AccountPage({Key? key, required this.user, required this.role})
      : super(key: key);

  @override
  State<AccountPage> createState() => _AccountPageState();
}

class _AccountPageState extends State<AccountPage> {
  List<Map<String, String>> allUsers = [];
  bool isLoading = false;

  @override
  void initState() {
    super.initState();
    if (widget.role == 'admin') {
      fetchAllUsers(); //ดึงข้อมูลผู้ใช้ทั้งหมด
    }
  }

  Future<void> fetchAllUsers() async {
    setState(() {
      isLoading = true;
    });

    final String url =
        'https://script.google.com/macros/s/AKfycbwqdzf3uekN9H025xXyzCgnwYeMSkKcfulvK2l5C0NirpQVn9G5r30DlP-iKOWkjjyw/exec';

    try {
      final response = await http.get(Uri.parse(url));
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        setState(() {
          allUsers = data.map<Map<String, String>>((user) {
            return {
              'name': user['name'].toString(),
              'username': user['username'].toString(),
              //'password': user['password'].toString(),
              'role': user['role'].toString(),
            };
          }).toList();
        });
      }
    } catch (e) {
      print("⚠️ Error fetching user list: $e");
    }

    setState(() {
      isLoading = false;
    });
  }

  void _confirmDelete(int index, String name) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text("Confirm to delete account"),
        content: Text("Are you sure want to delete $name"),
        actions: [
          TextButton(
            child: const Text("Cancel"),
            onPressed: () => Navigator.pop(context),
          ),
          TextButton(
            child: const Text("Delete", style: TextStyle(color: Colors.red)),
            onPressed: () async {
              Navigator.pop(context);
              await deleteUser(name); //Delete Account in Google sheet
              setState(() {
                allUsers.removeAt(index); // ลบจาก list ในแอป
              });
            },
          ),
        ],
      ),
    );
  }

  Future<void> deleteUser(String name) async {
    final url = Uri.parse(
      'https://script.google.com/macros/s/AKfycbwqdzf3uekN9H025xXyzCgnwYeMSkKcfulvK2l5C0NirpQVn9G5r30DlP-iKOWkjjyw/exec',
    );

    await http.post(url, body: {
      'action': 'delete',
      'name': name,
    });

    /*if (response.statusCode == 200) {
      final result = jsonDecode(response.body);
      print("✅ ${result['message']}");
    } else {
      print("❌ Failed to delete user");
    }*/
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Account'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            if (widget.role == 'admin')
              isLoading
                  ? const CircularProgressIndicator()
                  : Expanded(
                      child: ListView.builder(
                        itemCount: allUsers.length,
                        itemBuilder: (context, index) {
                          final user = allUsers[index];
                          final role = user['role'];
                          final icon = role == 'admin' ? '👑' : '👤';

                          return ListTile(
                            title: Text('$icon ${user['name']} ($role)'),
                            subtitle: Text('username: ${user['username']}'),
                            trailing: role != 'admin'
                                ? IconButton(
                                    icon: const Icon(Icons.delete,
                                        color: Colors.red),
                                    onPressed: () {
                                      _confirmDelete(index, user['name']!);
                                    },
                                  )
                                : null,
                          );
                        },
                      ),
                    )

            /*Column(
                children: [
                  Text(
                    'Name: ${widget.user}',
                    style: const TextStyle(fontSize: 20),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    'Role: ${widget.role}',
                    style: const TextStyle(fontSize: 20),
                  ),
                ],
              )*/
            else
              Column(
                children: [
                  IconButton(
                    icon: const Icon(Icons.directions_run),
                    iconSize: 150,
                    onPressed: () {},
                  ),
                  Text(
                    'Name: ${widget.user}',
                    style: const TextStyle(fontSize: 20),
                  ),
                ],
              )
          ],
        ),
      ),
    );
  }
}


/*
class AccountPage extends StatefulWidget {
  final String? user;

  const AccountPage(required user, {Key? key, this.user}) : super(key: key);

  @override
  State<AccountPage> createState() => _AccountPageState();
}

class _AccountPageState extends State<AccountPage> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Account'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            IconButton(
              icon: const Icon(Icons.directions_run),
              iconSize: 150,
              onPressed: () {},
            ),
            Text(
              'Username: ${widget.user}',
              style: const TextStyle(fontSize: 20),
            ),
          ],
        ),
      ),
    );
  }
}
*/
