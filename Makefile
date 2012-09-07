full: json-to-html dl_attachments fix_videos sync

full_light: json-to-html dl_attachments_light fix_videos sync

fix_videos_dev: fix_videos sync

json-to-html:
	./json-to-html-fragments.py -b out.json

dl_attachments:
	./dl_attachments.py -d out/

dl_attachments_light:
	./dl_attachments.py out/

fix_videos:
	./fix_videos.py out2/

sync:
	rsync -av out2/ ~/www/blog
