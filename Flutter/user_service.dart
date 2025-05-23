import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class UserService {
  // บันทึกข้อมูลผู้ใช้ใหม่
  Future<void> saveUser(String username, String password) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? userData = prefs.getString('users');
    Map<String, String> users =
        userData != null ? Map<String, String>.from(jsonDecode(userData)) : {};
    users[username] = password;
    await prefs.setString('users', jsonEncode(users));
  }

  // ตรวจสอบข้อมูลผู้ใช้
  Future<bool> validateUser(String username, String password) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? userData = prefs.getString('users');
    if (userData == null) return false;

    Map<String, String> users = Map<String, String>.from(jsonDecode(userData));
    return users.containsKey(username) && users[username] == password;
  }

  // ลบผู้ใช้ที่ระบุ
  Future<void> deleteUser(String username) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? userData = prefs.getString('users');
    if (userData == null) return;

    Map<String, String> users = Map<String, String>.from(jsonDecode(userData));
    users.remove(username);
    await prefs.setString('users', jsonEncode(users));
  }

  // ลบข้อมูลผู้ใช้ทั้งหมด
  Future<void> clearAllUsers() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.remove('users');
  }

  // ดึงรายชื่อผู้ใช้ทั้งหมด
  Future<List<String>> getAllUsers() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? userData = prefs.getString('users');
    if (userData == null) return [];
    Map<String, String> users = Map<String, String>.from(jsonDecode(userData));
    return users.keys.toList();
  }

  //ดึงทั้งUsernameและPassword
  Future<List<Map<String, String>>> getAllUserDetails() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? userData = prefs.getString('users');
    if (userData == null) return [];
    Map<String, String> users = Map<String, String>.from(jsonDecode(userData));

    // แปลงข้อมูลเป็น List<Map<String, String>> เพื่อรองรับการจัดรูปแบบ
    return users.entries
        .map((entry) => {"username": entry.key, "password": entry.value})
        .toList();
  }
}
