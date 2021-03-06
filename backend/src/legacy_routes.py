from flask import render_template, request, redirect, jsonify, url_for, session
from . import app
import simplejson as json

# DB
import pymysql
db = pymysql.connect(
  host="localhost",
  port=3306,
  user="page",
  passwd="page",
  db="page",
  charset="utf8"
)

# cors
from flask_cors import CORS, cross_origin
CORS(app, resources={r"*": {"origins": "http://localhost:8080"}})

# file
import os
import glob
ALLOWED_EXTENSIONS = {
  "document": {"txt", "pdf", "md", "docx", "pptx", "xlsx"},
  "image": {"png", "jpg", "jpeg", "gif", "bmp"},
  "audio": {"mp3", "flac", "wav", "ogg", "webm"},
  "video": {"mp4", "webm"},
}
def isAllowedFile(filename, rule):
  return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS[rule]
def getExtension(filename):
  return "." + filename.rsplit(".", 1)[1].lower()

# route
@app.route("/")
def home():
  return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
  if not request.is_json:
    return "Please request by JSON", 400
  
  username = request.json.get("username", None)
  password = request.json.get("password", None)
  
  try:
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM account WHERE username = %s AND password = %s", (username, password))
    account = cursor.fetchone()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()

  if account:
    session["loggedIn"] = True
    session["id"] = account["id"]
    session["username"] = account["username"]
    session["permission"] = account["permission"]
    return jsonify({
      "status": {
      "success": True,
      "message": "로그인 되었습니다",
    }}), 200

  return jsonify({
    "status": {
      "success": False,
      "message": "ID 또는 비밀번호를 다시 확인해 주십시오",
    }
  }), 200

@app.route("/checkSession", methods=["POST"])
def checkSession():
  if not request.is_json:
    return "Please request by JSON", 400

  if session:
    if session["loggedIn"] == True:
      return jsonify({
        "status": {
          "success": True,
          "message": "로그인이 되어 있습니다",
        },
        "auth": True,
      }), 200

  return jsonify({
    "status": {
      "success": True,
      "message": "로그인이 되어 있지 않습니다",
    },
    "auth": False,
  }), 200

@app.route("/logout", methods=["POST"])
def logout():
  if not request.is_json:
    return "Please request by JSON", 400
  session.clear()
  return jsonify({
    "status": {
      "success": True,
      "message": "로그아웃 되었습니다",
    }
  }), 200

@app.route("/getProfile", methods=["GET"])
def getProfile():
  try:
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM profile WHERE id = 1")
    profile = cursor.fetchone()
    db.commit()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()

  return jsonify({
    "status": {
      "success": True,
      "message": "프로필 조회 성공",
    },
    "profile": {
      "photo": profile["photo"],
      "codename": profile["codename"],
      "presentation": profile["presentation"]
    }
  }), 200

@app.route("/setCodename", methods=["POST"])
def setCodename():
  if not request.is_json:
    return "Please request by JSON", 400
  
  codename = request.json.get("codename", None)

  try:
    cursor = db.cursor()
    cursor.execute("UPDATE profile SET codename = %s WHERE id = 1", (codename))
    db.commit()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()

  return jsonify({
    "status": {
      "success": True,
      "message": "Github 코드네임이 변경 되었습니다",
    }
  }), 200

@app.route("/setPresentation", methods=["POST"])
def setPresentation():
  if not request.is_json:
    return "Please request by JSON", 400
  
  presentation = request.json.get("presentation", None)
  
  try:
    cursor = db.cursor()
    cursor.execute("UPDATE profile SET presentation = %s WHERE id = 1", (presentation))
    db.commit()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()

  return jsonify({
    "status": {
      "success": True,
      "message": "자기소개 메시지가 변경 되었습니다",
    }
  }), 200

@app.route("/setProfilePhoto", methods=["POST"])
def setProfilePhoto():
  # check if the post request has the file part
  if "file" not in request.files:
    return jsonify({
      "status": {
        "success": False,
        "message": "폼데이터에 파일이 없습니다",
      }
    }), 200
  newFile = request.files["file"]
  if newFile.filename == "":
    return jsonify({
      "status": {
        "success": False,
        "message": "파일이 선택되지 않았습니다",
      }
    }), 200
  if newFile and isAllowedFile(newFile.filename, "image") == True:
    # Create profile directory if not exist
    if not os.path.isdir(os.path.join(app.root_path, "view", "data")):
      os.mkdir(os.path.join(app.root_path, "view", "data"))
    if not os.path.isdir(os.path.join(app.root_path, "view", "data", "profile")):
      os.mkdir(os.path.join(app.root_path, "view", "data", "profile"))
    else:
      # Delete previous image file
      previousFile = glob.glob(os.path.join(app.root_path, "view", "data", "profile", "profilePhoto.*"))
      for targetFile in previousFile:
        os.remove(os.path.join(app.root_path, "view", "data", "profile", targetFile))

    filename = "profilePhoto" + getExtension(newFile.filename)
    newFile.save(os.path.join(app.root_path, "view", "data", "profile", filename))
    url = "data/profile/" + filename
    
    try:
      cursor = db.cursor()
      cursor.execute("UPDATE profile SET photo = %s WHERE id = 1", (url))
      db.commit()
    except Exception as error:
      print(error)
      return jsonify({
        "status": {
          "success": False,
          "message": "데이터베이스에 오류가 발생했습니다",
        }
      }), 200
    finally:
      cursor.close()

    return jsonify({
      "status": {
        "success": True,
        "message": "프로필 사진이 변경 되었습니다",
      },
      "url": url
    }), 200

  return jsonify({
    "status": {
      "success": False,
      "message": "허용되지 않는 파일입니다",
    }
  }), 200

@app.route("/getActivity", methods=["GET"])
def getActivity():
  try:
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM activity")
    activityList = cursor.fetchall()
    json.dumps( [dict(ix) for ix in activityList] )
    db.commit()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()

  return jsonify({
    "status": {
      "success": True,
      "message": "활동이력 조회 성공",
    },
    "activityList": activityList
  }), 200

@app.route("/createActivity", methods=["POST"])
def createActivity():
  if not request.is_json:
    return "Please request by JSON", 400
  
  activity = request.json

  try:
    cursor = db.cursor()
    cursor.execute("INSERT INTO activity (content, timestamp) VALUE (%s, %s)", (activity["content"], activity["timestamp"]))
    db.commit()
    cursor.execute("SELECT * FROM activity WHERE content = %s AND timestamp = %s", (activity["content"], activity["timestamp"]))
    activity = cursor.fetchone()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()
  print(activity)
  return jsonify({
    "status": {
      "success": True,
      "message": "활동이력이 추가 되었습니다",
    },
    "activity": {
      "id": activity[0],
      "content": activity[1],
      "timestamp": activity[2]
    }
  }), 200

@app.route("/modifyActivity", methods=["POST"])
def modifyActivity():
  if not request.is_json:
    return "Please request by JSON", 400
  
  activity = request.json

  try:
    cursor = db.cursor()
    cursor.execute("UPDATE activity SET content = %s, timestamp = %s WHERE id = %s", (activity["content"], activity["timestamp"], activity["id"]))
    db.commit()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()

  return jsonify({
    "status": {
      "success": True,
      "message": "활동이력이 수정 되었습니다",
    },
    "activity": activity
  }), 200

@app.route("/deleteActivity", methods=["POST"])
def deleteActivity():
  if not request.is_json:
    return "Please request by JSON", 400
  
  activityID = request.json.get("id", None)

  try:
    cursor = db.cursor()
    cursor.execute("DELETE FROM activity WHERE id = %s", (activityID))
    db.commit()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()

  return jsonify({
    "status": {
      "success": True,
      "message": "활동이력이 삭제 되었습니다",
    }
  }), 200

@app.route("/getSkillCategory", methods=["GET"])
def getSkillCategory():
  try:
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM skillcategory ORDER BY id")
    skillCategoryList = cursor.fetchall()
    json.dumps( [dict(ix) for ix in skillCategoryList] )
    db.commit()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()

  return jsonify({
    "status": {
      "success": True,
      "message": "카테고리 조회 성공",
    },
    "skillCategoryList": skillCategoryList
  }), 200

@app.route("/createSkillCategory", methods=["POST"])
def createSkillCategory():
  if not request.is_json:
    return "Please request by JSON", 400
  
  skillCategory = request.json

  try:
    cursor = db.cursor()
    cursor.execute("INSERT INTO skillCategory (category) VALUE (%s)", (skillCategory["category"]))
    db.commit()
    cursor.execute("SELECT * FROM skillCategory WHERE category = %s", (skillCategory["category"]))
    skillCategory = cursor.fetchone()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()
  print(skillCategory)
  return jsonify({
    "status": {
      "success": True,
      "message": "카테고리가 추가 되었습니다",
    },
    "skillCategory": {
      "id": skillCategory[0],
      "category": skillCategory[1]
    }
  }), 200

@app.route("/modifySkillCategory", methods=["POST"])
def modifySkillCategory():
  if not request.is_json:
    return "Please request by JSON", 400
  
  skillCategory = request.json

  try:
    cursor = db.cursor()
    cursor.execute("UPDATE skillCategory SET category = %s WHERE id = %s", (skillCategory["category"], skillCategory["id"]))
    db.commit()
    cursor.execute("SELECT * FROM skillCategory WHERE category = %s", (skillCategory["category"]))
    skillCategory = cursor.fetchone()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()
  print(skillCategory)
  return jsonify({
    "status": {
      "success": True,
      "message": "카테고리가 수정 되었습니다",
    },
    "skillCategory": {
      "id": skillCategory[0],
      "category": skillCategory[1]
    }
  }), 200

@app.route("/deleteSkillCategory", methods=["POST"])
def deleteSkillCategory():
  if not request.is_json:
    return "Please request by JSON", 400
  
  skillCategoryID = request.json.get("id", None)

  try:
    cursor = db.cursor()
    cursor.execute("DELETE FROM skillCategory WHERE id = %s", (skillCategoryID))
    db.commit()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()

  return jsonify({
    "status": {
      "success": True,
      "message": "카테고리가 삭제 되었습니다",
    }
  }), 200

@app.route("/getSkillList", methods=["GET"])
def getSkillList():
  try:
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM skill")
    skillList = cursor.fetchall()
    json.dumps( [dict(ix) for ix in skillList] )
    db.commit()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()

  return jsonify({
    "status": {
      "success": True,
      "message": "기술스택 조회 성공",
    },
    "skillList": skillList
  }), 200

@app.route("/uploadSkillImage", methods=["POST"])
def uploadSkillImage():
  if "file" not in request.files:
    return jsonify({
      "status": {
        "success": False,
        "message": "폼데이터에 파일이 없습니다",
      }
    }), 200
  newFile = request.files["file"]
  skillID = request.form["skillID"]
  print(skillID)
  if newFile.filename == "":
    return jsonify({
      "status": {
        "success": False,
        "message": "파일이 선택되지 않았습니다",
      }
    }), 200
  if newFile and isAllowedFile(newFile.filename, "image") == True:
    # Create profile directory if not exist
    if not os.path.isdir(os.path.join(app.root_path, "view", "data")):
      os.mkdir(os.path.join(app.root_path, "view", "data"))
    if not os.path.isdir(os.path.join(app.root_path, "view", "data", "skill")):
      os.mkdir(os.path.join(app.root_path, "view", "data", "skill"))
    else:
      # Delete previous image file
      previousFile = glob.glob(os.path.join(app.root_path, "view", "data", "skill", "skill_" + skillID + ".*"))
      for targetFile in previousFile:
        os.remove(os.path.join(app.root_path, "view", "data", "skill", targetFile))

    filename = "skill_" + skillID + getExtension(newFile.filename)
    newFile.save(os.path.join(app.root_path, "view", "data", "skill", filename))
    url = "data/skill/" + filename
  try:
    cursor = db.cursor()
    cursor.execute("UPDATE skill SET image = %s WHERE id = %s", (url, skillID))
    db.commit()
    cursor.execute("SELECT * FROM skill WHERE id = %s", skillID)
    skill = cursor.fetchone()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()
  
  return jsonify({
      "status": {
        "success": True,
        "message": "기술스택 이미지가 업로드 되었습니다",
      },
      "skill": {
        "id": skill[0],
        "name": skill[1],
        "category": skill[2],
        "image": skill[3]
      }
    }), 200

@app.route("/createSkill", methods=["POST"])
def createSkill():
  if not request.is_json:
    return "Please request by JSON", 400

  skill = request.json

  try:
    cursor = db.cursor()
    cursor.execute("INSERT INTO skill (name, category) VALUE (%s, %s)", (skill["name"], skill["category"]))
    db.commit()
    cursor.execute("SELECT id FROM skill WHERE name = %s", (skill["name"]))
    skillID = cursor.fetchone()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()
  
  print(skill)
  return jsonify({
    "status": {
      "success": True,
      "message": "기술스택이 추가 되었습니다, 파일을 업로드하세요",
    },
    "skillID": skillID
  }), 200

@app.route("/modifySkill", methods=["POST"])
def modifySkill():
  if not request.is_json:
    return "Please request by JSON", 400
  
  skill = request.json

  try:
    cursor = db.cursor()
    cursor.execute("UPDATE skill SET name = %s, category = %s WHERE id = %s", (skill["name"], skill["category"], skill["id"]))
    db.commit()
    cursor.execute("SELECT * FROM skill WHERE id = %s", skill["id"])
    skill = cursor.fetchone()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()
  
  print(skill)
  return jsonify({
    "status": {
      "success": True,
      "message": "기술스택이 수정 되었습니다",
    },
    "skill": {
      "id": skill[0],
      "name": skill[1],
      "category": skill[2],
      "image": skill[3]
    }
  }), 200

@app.route("/deleteSkill", methods=["POST"])
def deleteSkill():
  if not request.is_json:
    return "Please request by JSON", 400
  
  skillID = request.json.get("id", None)

  if os.path.isdir(os.path.join(app.root_path, "view", "data", "skill")):
    # Delete previous image file
    previousFile = glob.glob(os.path.join(app.root_path, "view", "data", "skill", "skill_" + str(skillID) + ".*"))
    print(previousFile)
    for targetFile in previousFile:
      os.remove(os.path.join(app.root_path, "view", "data", "skill", targetFile))

  try:
    cursor = db.cursor()
    cursor.execute("DELETE FROM skill WHERE id = %s", (skillID))
    db.commit()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()

  return jsonify({
    "status": {
      "success": True,
      "message": "기술스택이 삭제 되었습니다",
    }
  }), 200


@app.route("/getProjectCategory", methods=["GET"])
def getProjectCategory():
  try:
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM projectcategory ORDER BY id")
    projectCategoryList = cursor.fetchall()
    json.dumps( [dict(ix) for ix in projectCategoryList] )
    db.commit()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()

  return jsonify({
    "status": {
      "success": True,
      "message": "카테고리 조회 성공",
    },
    "projectCategoryList": projectCategoryList
  }), 200

@app.route("/createProjectCategory", methods=["POST"])
def createProjectCategory():
  if not request.is_json:
    return "Please request by JSON", 400
  
  projectCategory = request.json

  try:
    cursor = db.cursor()
    cursor.execute("INSERT INTO projectCategory (category) VALUE (%s)", (projectCategory["category"]))
    db.commit()
    cursor.execute("SELECT * FROM projectCategory WHERE category = %s", (projectCategory["category"]))
    projectCategory = cursor.fetchone()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()
  print(projectCategory)
  return jsonify({
    "status": {
      "success": True,
      "message": "카테고리가 추가 되었습니다",
    },
    "projectCategory": {
      "id": projectCategory[0],
      "category": projectCategory[1]
    }
  }), 200

@app.route("/modifyProjectCategory", methods=["POST"])
def modifyProjectCategory():
  if not request.is_json:
    return "Please request by JSON", 400
  
  projectCategory = request.json

  try:
    cursor = db.cursor()
    cursor.execute("UPDATE projectCategory SET category = %s WHERE id = %s", (projectCategory["category"], projectCategory["id"]))
    db.commit()
    cursor.execute("SELECT * FROM projectCategory WHERE category = %s", (projectCategory["category"]))
    projectCategory = cursor.fetchone()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()
  print(projectCategory)
  return jsonify({
    "status": {
      "success": True,
      "message": "카테고리가 수정 되었습니다",
    },
    "projectCategory": {
      "id": projectCategory[0],
      "category": projectCategory[1]
    }
  }), 200

@app.route("/deleteProjectCategory", methods=["POST"])
def deleteProjectCategory():
  if not request.is_json:
    return "Please request by JSON", 400
  
  projectCategoryID = request.json.get("id", None)

  try:
    cursor = db.cursor()
    cursor.execute("DELETE FROM projectCategory WHERE id = %s", (projectCategoryID))
    db.commit()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()

  return jsonify({
    "status": {
      "success": True,
      "message": "카테고리가 삭제 되었습니다",
    }
  }), 200

@app.route("/getProjectList", methods=["GET"])
def getProjectList():
  try:
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM project ORDER BY id")
    projectList = cursor.fetchall()
    json.dumps( [dict(ix) for ix in projectList] )
    db.commit()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()

  return jsonify({
    "status": {
      "success": True,
      "message": "기술스택 조회 성공",
    },
    "projectList": projectList
  }), 200

@app.route("/uploadProjectScreenshotImage", methods=["POST"])
def uploadProjectScreenshotImage():
  if "file" not in request.files:
    return jsonify({
      "status": {
        "success": False,
        "message": "폼데이터에 파일이 없습니다",
      }
    }), 200
  newFileList = request.files.getlist("file")
  projectID = request.form["projectID"]
  print(projectID)
  # Create profile directory if not exist
  if not os.path.isdir(os.path.join(app.root_path, "view", "data")):
    os.mkdir(os.path.join(app.root_path, "view", "data"))
  if not os.path.isdir(os.path.join(app.root_path, "view", "data", "project")):
    os.mkdir(os.path.join(app.root_path, "view", "data", "project"))
  if not os.path.isdir(os.path.join(app.root_path, "view", "data", "project", projectID)):
    os.mkdir(os.path.join(app.root_path, "view", "data", "project", projectID))
  # Delete previous image file
  previousFile = glob.glob(os.path.join(app.root_path, "view", "data", "project", projectID, "*.*"))
  for targetFile in previousFile:
    if os.path.exists(os.path.join(app.root_path, "view", "data", "project", projectID, targetFile)):
      os.remove(os.path.join(app.root_path, "view", "data", "project", projectID, targetFile))

  fileCount = 0
  urlList = []
  for newFile in newFileList:
    if newFile and isAllowedFile(newFile.filename, "image") == False:
      continue
    fileCount += 1
    filename = "project_screenshot_" + str(fileCount) + getExtension(newFile.filename)
    newFile.save(os.path.join(app.root_path, "view", "data", "project", projectID, filename))
    urlList.append("data/project/" + projectID + "/" + filename)

  try:
    cursor = db.cursor()
    cursor.execute("UPDATE project SET screenshot = %s WHERE id = %s", (json.dumps(urlList), projectID))
    db.commit()
    cursor.execute("SELECT * FROM project WHERE id = %s", projectID)
    project = cursor.fetchone()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()
  
  return jsonify({
      "status": {
        "success": True,
        "message": "프로젝트 스크린샷 이미지가 업로드 되었습니다",
      },
      "project": {
        "id": project[0],
        "name": project[1],
        "category": project[2],
        "link": project[3],
        "discription": project[4],
        "content": project[5],
        "screenshot": project[6],
        "stackTags": project[7]
      }
    }), 200

@app.route("/createProject", methods=["POST"])
def createProject():
  if not request.is_json:
    return "Please request by JSON", 400

  project = request.json

  # 쉼표로 구분된 게시물 태그를 공백 무시하고 쉼표 기준으로 리스트로 변환
  stackTagList = project["stackTags"].replace(" ", "").split(",")

  try:
    cursor = db.cursor()
    cursor.execute("INSERT INTO project (name, category, link, discription, content, tags) VALUE (%s, %s, %s, %s, %s, %s)", (project["name"], project["category"], project["link"], project["discription"], project["content"], json.dumps(stackTagList)))
    db.commit()
    cursor.execute("SELECT id FROM project WHERE name = %s", (project["name"]))
    projectID = cursor.fetchone()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()
  
  print(project)
  return jsonify({
    "status": {
      "success": True,
      "message": "프로젝트 상세정보가 추가 되었습니다, 파일을 업로드하세요",
    },
    "projectID": projectID
  }), 200

@app.route("/modifyProject", methods=["POST"])
def modifyProject():
  if not request.is_json:
    return "Please request by JSON", 400
  
  project = request.json

  # 쉼표로 구분된 게시물 태그를 공백 무시하고 쉼표 기준으로 리스트로 변환
  print(type(project["stackTags"]))
  if type(project["stackTags"]) == list:
    stackTagList = project["stackTags"]
  else:
    stackTagList = project["stackTags"].replace(" ", "").split(",")

  try:
    cursor = db.cursor()
    cursor.execute("UPDATE project SET name = %s, category = %s, link = %s, discription = %s, content = %s, tags = %s WHERE id = %s", (project["name"], project["category"], project["link"], project["discription"], project["content"], json.dumps(stackTagList), project["id"]))
    db.commit()
    cursor.execute("SELECT * FROM project WHERE id = %s", project["id"])
    project = cursor.fetchone()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()
  
  print(project)
  return jsonify({
    "status": {
      "success": True,
      "message": "프로젝트 상세정보가 변경 되었습니다",
    },
    "project": {
      "id": project[0],
      "name": project[1],
      "category": project[2],
      "link": project[3],
      "discription": project[4],
      "content": project[5],
      "screenshot": project[6],
      "stackTags": project[7]
    }
  }), 200

@app.route("/deleteProject", methods=["POST"])
def deleteProject():
  if not request.is_json:
    return "Please request by JSON", 400
  
  projectID = request.json.get("id", None)

  if os.path.isdir(os.path.join(app.root_path, "view", "data", "project", str(projectID))):
    # Delete previous image file
    previousFile = glob.glob(os.path.join(app.root_path, "view", "data", "project", str(projectID) + "*.*"))
    print(previousFile)
    for targetFile in previousFile:
      os.remove(os.path.join(app.root_path, "view", "data", "project", str(projectID), targetFile))

  try:
    cursor = db.cursor()
    cursor.execute("DELETE FROM project WHERE id = %s", (projectID))
    db.commit()
  except Exception as error:
    print(error)
    return jsonify({
      "status": {
        "success": False,
        "message": "데이터베이스에 오류가 발생했습니다",
      }
    }), 200
  finally:
    cursor.close()

  return jsonify({
    "status": {
      "success": True,
      "message": "프로젝트 상세정보가 삭제 되었습니다",
    }
  }), 200
