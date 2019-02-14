from PySide import QtGui, QtCore
#import sip

import maya.cmds as mc
import maya.OpenMaya as om 
import maya.OpenMayaUI as mui


class Outliner(QtGui.QDialog):
	"""
	Outliner(QtGui.QDialog)
	Custom dialog widget that emulates a few baisc functions of the maya outliner
	"""
	def __init__(self, *args, **Kwargs):
		super(Outliner, self).__init__(*args, **Kwargs)

		self.resize(200, 500)
		self.setObjectName('CustomOutliner')

		self.layout = QtGui.QVBoxLayout(self)
		self.layout.setContentsMargins(2, 2, 2, 2)
		self.model = QtGui.QStandardItemModel()
		self.model.setItemPrototype(DagTreeItem())

		view = QtGui.QTreeView()
		view.setModel(self.model)
		view.header().setVisible(False)
		view.setEditTriggers(view.NoEditTriggers)
		view.setSelectionMode(view.ExtendedSelection)

		self.view = view
		self.layout.addWidget(self.view)

		QtCore.QTimer.singleShot(1, self.initDisplay)

		self.view.expanded.connect(self.nodeExpanded)
		#self.view.selectionModel().selectionChanged.connect(self.selectionChanged)
		view.connect(view.selectionModel(),
					 QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"), 
					 self.selectionChanged)


	def nodeExpanded(self, idx):
		"""
		nodeExpanded(self, idx)

		Solt to handle an item in the list being expanded.
		Populates the children of this items immediate children.
		"""
		item = self.model.itemFromIndex(idx)

		if item.hasChildren():

			for row in xrange(item.rowCount()):
				child = item.child(row)
				child.removeRows(0, child.rowCount())
				grandChildren = self.scanDag(child)
				if grandChildren:
					child.appendRows(grandChildren)

	def selectionChanged(self):
		"""
		selectionChanged()

		Slot called when the sleection of the view has changed.
		Selects the corresponding nodes in the Maya scene that 
		match the selected view items.
		"""
		nodes = [self.model.itemFromIndex(i).fullname for i in self.view.selectedIndexes()]
		if nodes:
			mc.select(nodes, replace=True)
		else:
			mc.select(clear=True)


	def initDisplay(self):
		"""
		Initialize the model with the root world items
		"""
		self.model.clear()

		excludes = set([
			'|groundPlane_transform',
			'|Manipulator1',
			'|UniversalManip',
			'|CubeCompass'])

		roots = self.scanDag(mindepth=1, maxdepth=2, exclude=excludes)
		if roots:
			self.model.appendColumn(roots)

	@staticmethod
	def scanDag(root=None, mindepth=1, maxdepth=1, exclude=None):
		"""
		scanDag(root=None, mindepth=1, maxdepth=1, exclude=None)

		root 			-either an MDapgPath or DagTreeItem to start from
		mindepth 		-starting depth of items to return (defualt 1; immediate children)
		maxdepth 		-ending depth of items to return (defualt 1; immediate children)
		exclude 		-a sequence of strings representing node paths that should be skipped

		walks the DAG tree from a starting root, through a given depth
		range. Returns a list of the top levcel children of the root as DagTreeItem's.and
		Decendants of these items already have been added as DagTreeItem children.and

		mindepth or maxdepth may be set to -1, in which case those limits will be ignored
		altogether.
		"""

		# Allow either a DagTreeItem or an MDagPath
		if isinstance(root, DagTreeItem):
			root = root.dagObj

		dagIt = om.MItDag()
		root = root or dagIt.root()
		exclude = exclude or set()

		dagIt.reset(root, om.MItDag.kDepthFirst)

		# These will be our final top-most nodes from the search
		nodes = []

		# This will map node string paths to the items to help us
		# easily look up a parent at any point in the search.
		itemMap = {}

		while not dagIt.isDone():

			depth = dagIt.depth() 
			# If the iterator has gone past our target
			# Depth, prune out the tree from here on down,
			# so it is not used in futre loops
			if (maxdepth > -1) and (depth > maxdepth):
				dagIt.prune()

			# This would allow us to skip past an amount of
			# levels from the root, if mindepth > 1
			elif depth >= mindepth:
				dagPath = om.MDagPath()
				dagIt.getPath(dagPath)
				path = dagPath.fullPathName()

				if path and path not in exclude:
					item = DagTreeItem(dagPath)

					#save this item in our mapping
					itemMap[item.fullname] = item

					# If this item has a parent, add it to that
					# parent DagTreeItem.
					# Otherwise, just add it to our top level list
					parent = itemMap.get(item.parentname)
					if parent:
						parent.appendRow(item)
					else:
						nodes.append(item)
				else:
					dagIt.prune()

			dagIt.next()
		return nodes

class DagTreeItem(QtGui.QStandardItem):
	"""
	DagTreeItem(QtGui.QStandardItem)
	This represents a Dag Node
	"""
	def __init__(self, dagObj=None):
		super(DagTreeItem, self).__init__()

		self.dagObj = dagObj
		self.setText(self.name)

	def __repr__(self):
		return '{}: {}'.format(self.__class__.__name__, self.name)

	@property
	def fullname(self):
		if not self.dagObj:
			return ''
		return self.dagObj.fullPathName()

	@property
	def name(self):
		return self.fullname.rsplit('|', 1)[-1]

	@property
	def parentname(self):
		return self.fullname.rsplit('|', 1)[0]
	
	




	
